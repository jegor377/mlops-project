import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlencode
from typing import cast

import stripe

from src.ml_server.conf.settings import Settings
from src.ml_server.models.user import User
from src.ml_server.models.audit_log import EventCategory

from src.ml_server.dependencies.settings import get_settings
from src.ml_server.dependencies.db import get_session
from src.ml_server.dependencies.current_user import get_current_user

from src.ml_server.services.audit_log import log_event
from src.ml_server.services import billing as billing_services

from src.ml_server.utils.frontend_urls import FrontendURLs


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/checkout/complete")
async def checkout_complete(
    req: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    if not user.pending_checkout:
        raise HTTPException(status_code=400, detail="No pending checkout for this user.")

    try:
        plan = await billing_services.get_pro_plan(session)

        if plan.stripe_price_id is None:
            logger.error(f"Strip price id is None in the plan with id = {plan.id}")
            raise HTTPException(status_code=500, detail="Checkout is not available right now.")

        customer_id = await billing_services.ensure_stripe_customer(session, user, settings)

        success_url = settings.hostname
        success_url += req.app.url_path_for("checkout_success")
        success_url += "?session_id={CHECKOUT_SESSION_ID}"

        cancel_url = settings.hostname + req.app.url_path_for("checkout_stripe_cancel")

        checkout_session = await billing_services.create_checkout_session(
            settings=settings,
            customer_id=customer_id,
            price_id=plan.stripe_price_id,
            user_id=user.id,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except ValueError as e:
        logger.error(f"Checkout misconfiguration: {e}")
        raise HTTPException(status_code=500, detail="Checkout is not available right now.")
    except stripe.StripeError as e:
        logger.error(f"Stripe error creating checkout session for user {user.id}: {e}")
        await session.rollback()
        raise HTTPException(status_code=502, detail="Could not start checkout.")

    await log_event(
        db=session,
        user_id=user.id,
        event=EventCategory.billing_checkout_started,
        request=req,
    )

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to persist stripe customer for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if checkout_session.url is None:
        logger.error(f"Checkout sessions's url is None for user with id = {user.id}")
        raise HTTPException(status_code=500, detail="Checkout is not available right now.")

    return RedirectResponse(url=checkout_session.url, status_code=303)


@router.post("/checkout/cancel", status_code=200)
async def checkout_cancel(
    req: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user.pending_checkout = False

    await log_event(
        db=session,
        user_id=user.id,
        event=EventCategory.billing_checkout_canceled,
        request=req,
    )

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to cancel pending checkout for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return Response(status_code=200)


@router.get("/billing/success", name="checkout_success")
async def checkout_success(
    settings: Annotated[Settings, Depends(get_settings)],
    session_id: Annotated[str | None, Query()] = None,
):
    redirect_uri = settings.frontend_hostname + FrontendURLs.BILLING
    redirect_uri += "?" + urlencode({"checkout": "success"})
    return RedirectResponse(url=redirect_uri)


@router.get("/billing/cancel", name="checkout_stripe_cancel")
async def checkout_stripe_cancel(
    settings: Annotated[Settings, Depends(get_settings)],
):
    redirect_uri = settings.frontend_hostname + FrontendURLs.BILLING
    redirect_uri += "?" + urlencode({"checkout": "canceled"})
    return RedirectResponse(url=redirect_uri)


@router.post("/billing/webhook", status_code=200)
async def stripe_webhook(
    req: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    payload = await req.body()
    sig_header = req.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header.")

    try:
        event = billing_services.construct_webhook_event(payload, sig_header, settings)
    except (ValueError, stripe.SignatureVerificationError) as e:
        logger.error(f"Invalid Stripe webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload.")

    try:
        if event.type == "checkout.session.completed":
            checkout_session: stripe.checkout.Session = cast(
                stripe.checkout.Session,
                event.data.object
            )
            user_id = (
                checkout_session.metadata['user_id']
                if checkout_session.metadata and 'user_id' in checkout_session.metadata
                else None
            )
            await billing_services.handle_checkout_session_completed(session, settings, checkout_session)
            event_category = EventCategory.billing_subscription_activated
        elif event.type == "customer.subscription.updated":
            subscription = stripe.Subscription = cast(
                stripe.Subscription,
                event.data.object
            )
            user_id = (
                subscription.metadata['user_id']
                if subscription.metadata and 'user_id' in subscription.metadata
                else None
            )
            await billing_services.handle_subscription_updated(session, settings, subscription)
            event_category = EventCategory.billing_subscription_updated
        elif event.type == "customer.subscription.deleted":
            subscription = stripe.Subscription = cast(
                stripe.Subscription,
                event.data.object
            )
            user_id = (
                subscription.metadata['user_id']
                if subscription.metadata and 'user_id' in subscription.metadata
                else None
            )
            await billing_services.handle_subscription_deleted(session, subscription)
            event_category = EventCategory.billing_subscription_canceled
        else:
            return Response(status_code=200)

        await session.flush()

        if user_id is not None and isinstance(user_id, str) and user_id.isnumeric():
            user_id = int(user_id)
            await log_event(db=session, user_id=user_id, event=event_category, request=req)
        else:
            logger.error(f"Could not infer user id from webhook event data object, which prevented logging billing event: {event.data.object}")
        
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"IntegrityError handling Stripe event {event.type}: {e.orig}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error handling Stripe event {event.type}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return Response(status_code=200)
