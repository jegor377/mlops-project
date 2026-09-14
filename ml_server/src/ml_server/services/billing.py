import logging
from datetime import datetime, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml_server.conf.settings import Settings
from src.ml_server.models.user import User
from src.ml_server.models.plan import Plan
from src.ml_server.models.subscription import Subscription, SubscriptionStatus
from src.ml_server.enums.plan_tier import PlanTier

logger = logging.getLogger(__name__)

STRIPE_TO_LOCAL_STATUS: dict[str, SubscriptionStatus] = {
    "active": SubscriptionStatus.ACTIVE,
    "trialing": SubscriptionStatus.TRIALING,
    "past_due": SubscriptionStatus.PAST_DUE,
    "unpaid": SubscriptionStatus.PAST_DUE,
    "incomplete": SubscriptionStatus.PAST_DUE,
    "incomplete_expired": SubscriptionStatus.CANCELED,
    "canceled": SubscriptionStatus.CANCELED,
}


async def seed_default_plans(session: AsyncSession, settings: Settings) -> None:
    """Seed Free and Pro plans on startup if they don't exist."""
    # Check if Free plan exists
    result = await session.execute(select(Plan).where(Plan.tier == PlanTier.FREE))
    free_plan = result.scalar_one_or_none()

    if free_plan is None:
        # Create Free plan with default limits
        free_plan = Plan(
            tier=PlanTier.FREE,
            name="Free",
            price_cents=0,
            stripe_price_id=None,
            requests_per_day=None,  # unlimited
            api_key_limit=None,     # unlimited
            history_days=None,      # unlimited
            priority_support=False,
            webhook_notifications=False,
            dedicated_support=False,
            custom_sla=False,
            on_prem=False,
            is_active=True,
        )
        session.add(free_plan)
        await session.flush()

    # Check if Pro plan exists
    result = await session.execute(select(Plan).where(Plan.tier == PlanTier.PRO))
    pro_plan = result.scalar_one_or_none()

    if pro_plan is None:
        # Create Pro plan if stripe_price_id is configured
        if settings.stripe.price_id is None:
            logger.warning("Pro plan not configured - stripe_price_id not set")
            return

        pro_plan = Plan(
            tier=PlanTier.PRO,
            name="Pro",
            price_cents=None,  # Negotiated via Stripe
            stripe_price_id=settings.stripe.price_id.get_secret_value(),
            requests_per_day=None,  # unlimited
            api_key_limit=None,     # unlimited
            history_days=None,      # unlimited
            priority_support=True,
            webhook_notifications=True,
            dedicated_support=False,
            custom_sla=False,
            on_prem=False,
            is_active=True,
        )
        session.add(pro_plan)
        await session.flush()
    elif pro_plan.stripe_price_id is None:
        # Update Pro plan if price_id is configured but not set
        if settings.stripe.price_id is not None:
            pro_plan.stripe_price_id = settings.stripe.price_id.get_secret_value()
            await session.flush()


async def get_pro_plan(session: AsyncSession) -> Plan:
    result = await session.execute(
        select(Plan).where(Plan.tier == PlanTier.PRO, Plan.is_active.is_(True))
    )
    plan = result.scalar_one_or_none()
    if plan is None or not plan.stripe_price_id:
        raise ValueError("Pro plan is not configured with a Stripe price id")
    return plan


async def ensure_stripe_customer(
    session: AsyncSession, user: User, settings: Settings
) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = await stripe.Customer.create_async(
        api_key=settings.stripe.secret_key.get_secret_value(),
        email=user.email,
        metadata={"user_id": str(user.id)},
    )
    stripe_customer_id: str = customer["id"]
    user.stripe_customer_id = stripe_customer_id
    await session.flush()
    return stripe_customer_id


async def create_checkout_session(
    *,
    settings: Settings,
    customer_id: str,
    price_id: str,
    user_id: int,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    return await stripe.checkout.Session.create_async(
        api_key=settings.stripe.secret_key.get_secret_value(),
        mode="subscription",
        customer=customer_id,
        client_reference_id=str(user_id),
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user_id)},
    )


async def create_upgrade_checkout_session(
    *,
    settings: Settings,
    session: AsyncSession,
    user: User,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """
    Create a checkout session for upgrading an existing subscription to Pro plan.

    If the user has an existing subscription with a Stripe ID, this creates an upgrade
    session that updates the existing subscription. Otherwise, it creates a standard
    subscription session.
    """
    # Get Pro plan from database
    pro_plan = await get_pro_plan(session)

    # Ensure Stripe customer exists for user
    customer_id = await ensure_stripe_customer(session, user, settings)

    # Check if user has an existing subscription with Stripe ID
    result = await session.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.stripe_subscription_id.is_not(None)
        ).order_by(Subscription.created_at.desc())
    )
    existing_subscription = result.scalar_one_or_none()

    # Build line items for Pro plan
    line_items = [{"price": pro_plan.stripe_price_id, "quantity": 1}]

    if existing_subscription:
        # If user has existing subscription with Stripe ID, create upgrade session
        # with subscription_data metadata to update the existing subscription
        return await stripe.checkout.Session.create_async(
            api_key=settings.stripe.secret_key.get_secret_value(),
            mode="subscription",
            customer=customer_id,
            subscription=existing_subscription.stripe_subscription_id,
            subscription_data={
                "metadata": {
                    "user_id": str(user.id),
                    "is_upgrade": "true",
                    "current_subscription_id": existing_subscription.stripe_subscription_id,
                }
            },
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user.id), "is_upgrade": "true"},
        )
    else:
        # If no existing subscription, create standard session
        return await stripe.checkout.Session.create_async(
            api_key=settings.stripe.secret_key.get_secret_value(),
            mode="subscription",
            customer=customer_id,
            client_reference_id=str(user.id),
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user.id), "is_upgrade": "false"},
        )


def construct_webhook_event(
    payload: bytes, sig_header: str, settings: Settings
) -> stripe.Event:
    return stripe.Webhook.construct_event(
        payload,
        sig_header,
        settings.stripe.webhook_secret.get_secret_value(),
    )


async def _upsert_subscription_from_stripe(
    session: AsyncSession,
    *,
    user_id: int,
    plan_id: int,
    stripe_subscription_id: str,
    settings: Settings,
) -> Subscription:
    stripe_sub = await stripe.Subscription.retrieve_async(
        stripe_subscription_id,
        api_key=settings.stripe.secret_key.get_secret_value(),
    )

    result = await session.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_subscription_id=stripe_subscription_id,
        )
        session.add(subscription)

    subscription.status = STRIPE_TO_LOCAL_STATUS.get(
        stripe_sub["status"], SubscriptionStatus.ACTIVE
    )
    current_period_end = stripe_sub["items"]["data"][0]["current_period_end"]
    if current_period_end:
        subscription.current_period_end = datetime.fromtimestamp(
            current_period_end, tz=timezone.utc
        )

    return subscription


async def handle_checkout_session_completed(
    session: AsyncSession, settings: Settings, checkout_session: stripe.checkout.Session
) -> None:
    user_id_raw = checkout_session.client_reference_id or (
        checkout_session.metadata["user_id"]
        if checkout_session.metadata and "user_id" in checkout_session.metadata
        else None
    )
    stripe_subscription_id = str(checkout_session.subscription) if checkout_session.subscription else None
    stripe_customer_id = str(checkout_session.customer) if checkout_session.customer else None

    if not user_id_raw or not stripe_subscription_id:
        logger.error(f"checkout.session.completed missing user/subscription refs: {checkout_session}")
        return

    user_id = int(user_id_raw)
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        logger.error(f"checkout.session.completed for unknown user {user_id}")
        return

    if stripe_customer_id and not user.stripe_customer_id:
        user.stripe_customer_id = stripe_customer_id

    plan = await get_pro_plan(session)

    # Check if this is an upgrade checkout session
    is_upgrade = (
        checkout_session.metadata and 
        checkout_session.metadata.get("is_upgrade") == "true"
    )

    if is_upgrade:
        # For upgrade sessions, we need to update the existing subscription
        # by extracting current_subscription_id from metadata
        current_subscription_id = (
            checkout_session.metadata.get("current_subscription_id")
            if checkout_session.metadata
            else None
        )
        
        if current_subscription_id:
            # Update existing subscription to Pro plan
            result = await session.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == current_subscription_id
                )
            )
            subscription = result.scalar_one_or_none()
            if subscription:
                subscription.plan_id = plan.id
                subscription.status = STRIPE_TO_LOCAL_STATUS.get(
                    checkout_session.subscription.status if checkout_session.subscription else "active",
                    SubscriptionStatus.ACTIVE
                )
                if checkout_session.subscription:
                    current_period_end = checkout_session.subscription.items.data[0].current_period_end
                    if current_period_end:
                        subscription.current_period_end = datetime.fromtimestamp(
                            current_period_end, tz=timezone.utc
                        )
            else:
                logger.warning(f"Upgrade session referenced non-existent subscription {current_subscription_id}")
                # Fallback to creating new subscription if upgrade target not found
                await _upsert_subscription_from_stripe(
                    session,
                    user_id=user.id,
                    plan_id=plan.id,
                    stripe_subscription_id=stripe_subscription_id,
                    settings=settings,
                )
        else:
            # No existing subscription ID, create new subscription
            await _upsert_subscription_from_stripe(
                session,
                user_id=user.id,
                plan_id=plan.id,
                stripe_subscription_id=stripe_subscription_id,
                settings=settings,
            )
    else:
        # Standard checkout flow - create new subscription
        await _upsert_subscription_from_stripe(
            session,
            user_id=user.id,
            plan_id=plan.id,
            stripe_subscription_id=stripe_subscription_id,
            settings=settings,
        )

    user.pending_checkout = False


async def handle_subscription_updated(
    session: AsyncSession, settings: Settings, stripe_subscription: stripe.Subscription
) -> None:
    stripe_subscription_id = stripe_subscription.id
    if not stripe_subscription_id:
        return

    result = await session.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        logger.warning(f"subscription.updated for unknown stripe_subscription_id {stripe_subscription_id}")
        return

    event_status: str | None = stripe_subscription.status
    if event_status is None:
        logger.warning(
            f"subscription.updated status is null for stripe_subscription_id {stripe_subscription_id}")
        return

    subscription.status = STRIPE_TO_LOCAL_STATUS.get(
        event_status, subscription.status
    )
    current_period_end = stripe_subscription.items.data[0].current_period_end
    if current_period_end:
        subscription.current_period_end = datetime.fromtimestamp(
            current_period_end, tz=timezone.utc
        )


async def handle_subscription_deleted(
    session: AsyncSession, stripe_subscription: stripe.Subscription
) -> None:
    stripe_subscription_id = stripe_subscription.id
    if not stripe_subscription_id:
        return

    result = await session.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return

    subscription.status = SubscriptionStatus.CANCELED
    subscription.canceled_at = datetime.now(timezone.utc)
