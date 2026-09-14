"""
Tests for the checkout.session.completed webhook handler and the
handle_checkout_session_completed() service function.

Covers:
  - Standard (non-upgrade) checkout: new subscription created (Req 3.1, 3.2, 3.3)
  - Upgrade checkout: existing subscription updated to Pro plan (Req 5.4)
  - Upgrade checkout with CANCELED subscription: new subscription created (Req 5.5)
  - Upgrade checkout referencing unknown subscription: new subscription created (Req 3.6)
  - Missing user_id in metadata: early exit, no crash (Req 3.6)
  - Unknown user_id in metadata: early exit, no crash (Req 3.6)
  - user.pending_checkout set to False in all success cases (Req 3.1)
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import stripe
from sqlalchemy import select

from src.ml_server.enums.plan_tier import PlanTier
from src.ml_server.models.plan import Plan
from src.ml_server.models.subscription import Subscription, SubscriptionStatus
from src.ml_server.models.user import User
from src.ml_server.services import billing as billing_services
from src.tests.conftest import make_classic_user, make_plan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_STRIPE_SUB_ID = "sub_test_12345"
FAKE_STRIPE_SUB_ID_NEW = "sub_test_99999"
FAKE_STRIPE_CUSTOMER_ID = "cus_test_abc"
FAKE_PERIOD_END = int(datetime(2099, 1, 1, tzinfo=timezone.utc).timestamp())


def _make_stripe_subscription_mock(
    stripe_id: str = FAKE_STRIPE_SUB_ID,
    status: str = "active",
    period_end: int = FAKE_PERIOD_END,
) -> MagicMock:
    """Build a minimal mock that looks like a Stripe Subscription object."""
    item = MagicMock()
    item.current_period_end = period_end

    items = MagicMock()
    items.data = [item]

    sub = MagicMock()
    sub.id = stripe_id
    sub.__getitem__ = lambda self, key: {  # type: ignore[misc]
        "status": status,
        "items": {"data": [{"current_period_end": period_end}]},
    }[key]
    sub.items = items
    sub.status = status
    return sub


def _make_checkout_session(
    user_id: int,
    stripe_subscription_id: str = FAKE_STRIPE_SUB_ID,
    is_upgrade: bool = False,
    current_subscription_id: str | None = None,
    customer_id: str = FAKE_STRIPE_CUSTOMER_ID,
) -> MagicMock:
    """Build a minimal mock that looks like a Stripe Checkout Session object."""
    session = MagicMock(spec=stripe.checkout.Session)
    session.client_reference_id = str(user_id) if not is_upgrade else None
    session.subscription = stripe_subscription_id
    session.customer = customer_id

    metadata: dict[str, str] = {"user_id": str(user_id)}
    if is_upgrade:
        metadata["is_upgrade"] = "true"
        if current_subscription_id:
            metadata["current_subscription_id"] = current_subscription_id
    else:
        metadata["is_upgrade"] = "false"

    session.metadata = metadata
    return session


async def _make_pro_plan(session, stripe_price_id: str = "price_pro_123") -> Plan:
    plan = Plan(
        tier=PlanTier.PRO,
        name="Pro",
        price_cents=None,
        stripe_price_id=stripe_price_id,
        requests_per_day=None,
        api_key_limit=None,
        history_days=None,
        priority_support=True,
        webhook_notifications=True,
        dedicated_support=False,
        custom_sla=False,
        on_prem=False,
        is_active=True,
    )
    session.add(plan)
    await session.flush()
    return plan


async def _make_subscription(
    session,
    user: User,
    plan: Plan,
    stripe_subscription_id: str | None = FAKE_STRIPE_SUB_ID,
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
) -> Subscription:
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        stripe_subscription_id=stripe_subscription_id,
        status=status,
    )
    session.add(sub)
    await session.flush()
    return sub


# ---------------------------------------------------------------------------
# Tests for handle_checkout_session_completed()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_standard_checkout_creates_new_subscription(db_session, test_settings):
    """
    Req 3.1, 3.2, 3.3: Standard (non-upgrade) checkout.session.completed
    creates a new local subscription with correct status and period_end.
    """
    user = await make_classic_user(db_session)
    user.pending_checkout = True
    pro_plan = await _make_pro_plan(db_session)
    await db_session.flush()

    checkout_session = _make_checkout_session(user_id=user.id, is_upgrade=False)

    stripe_sub_mock = _make_stripe_subscription_mock(
        stripe_id=FAKE_STRIPE_SUB_ID, status="active"
    )

    with patch.object(
        stripe.Subscription,
        "retrieve_async",
        new=AsyncMock(return_value=stripe_sub_mock),
    ):
        await billing_services.handle_checkout_session_completed(
            db_session, test_settings, checkout_session
        )

    # Subscription created
    result = await db_session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()
    assert subscription is not None
    assert subscription.plan_id == pro_plan.id
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.stripe_subscription_id == FAKE_STRIPE_SUB_ID
    expected_end = datetime.fromtimestamp(FAKE_PERIOD_END, tz=timezone.utc)
    assert subscription.current_period_end == expected_end

    # pending_checkout cleared
    assert user.pending_checkout is False


@pytest.mark.asyncio
async def test_upgrade_checkout_updates_existing_subscription(db_session, test_settings):
    """
    Req 5.4: Upgrade checkout.session.completed updates the existing subscription
    to the Pro plan instead of creating a duplicate.
    """
    user = await make_classic_user(db_session)
    user.pending_checkout = True
    free_plan = await make_plan(db_session, tier=PlanTier.FREE, name="Free")
    pro_plan = await _make_pro_plan(db_session)
    existing_sub = await _make_subscription(
        db_session, user, free_plan, stripe_subscription_id=FAKE_STRIPE_SUB_ID
    )
    await db_session.flush()

    checkout_session = _make_checkout_session(
        user_id=user.id,
        stripe_subscription_id=FAKE_STRIPE_SUB_ID,
        is_upgrade=True,
        current_subscription_id=FAKE_STRIPE_SUB_ID,
    )

    stripe_sub_mock = _make_stripe_subscription_mock(
        stripe_id=FAKE_STRIPE_SUB_ID, status="active"
    )

    with patch.object(
        stripe.Subscription,
        "retrieve_async",
        new=AsyncMock(return_value=stripe_sub_mock),
    ):
        await billing_services.handle_checkout_session_completed(
            db_session, test_settings, checkout_session
        )

    # No duplicate subscription created — still exactly 1 subscription for user
    result = await db_session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscriptions = result.scalars().all()
    assert len(subscriptions) == 1

    # Existing subscription updated to Pro plan
    updated = subscriptions[0]
    assert updated.id == existing_sub.id
    assert updated.plan_id == pro_plan.id
    assert updated.status == SubscriptionStatus.ACTIVE

    # pending_checkout cleared
    assert user.pending_checkout is False


@pytest.mark.asyncio
async def test_upgrade_checkout_with_canceled_subscription_creates_new(
    db_session, test_settings
):
    """
    Req 5.5: Upgrade checkout where the existing subscription is CANCELED
    should create a new subscription, not update the canceled one.
    """
    user = await make_classic_user(db_session)
    user.pending_checkout = True
    free_plan = await make_plan(db_session, tier=PlanTier.FREE, name="Free")
    pro_plan = await _make_pro_plan(db_session)
    canceled_sub = await _make_subscription(
        db_session,
        user,
        free_plan,
        stripe_subscription_id=FAKE_STRIPE_SUB_ID,
        status=SubscriptionStatus.CANCELED,
    )
    await db_session.flush()

    # Webhook arrives with a NEW stripe_subscription_id (Stripe created a new sub)
    checkout_session = _make_checkout_session(
        user_id=user.id,
        stripe_subscription_id=FAKE_STRIPE_SUB_ID_NEW,
        is_upgrade=True,
        current_subscription_id=FAKE_STRIPE_SUB_ID,
    )

    stripe_sub_mock = _make_stripe_subscription_mock(
        stripe_id=FAKE_STRIPE_SUB_ID_NEW, status="active"
    )

    with patch.object(
        stripe.Subscription,
        "retrieve_async",
        new=AsyncMock(return_value=stripe_sub_mock),
    ):
        await billing_services.handle_checkout_session_completed(
            db_session, test_settings, checkout_session
        )

    result = await db_session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscriptions = result.scalars().all()

    # Two subscriptions: the old CANCELED one + the new ACTIVE one
    assert len(subscriptions) == 2

    new_sub = next(s for s in subscriptions if s.id != canceled_sub.id)
    assert new_sub.plan_id == pro_plan.id
    assert new_sub.status == SubscriptionStatus.ACTIVE
    assert new_sub.stripe_subscription_id == FAKE_STRIPE_SUB_ID_NEW

    # Original canceled subscription remains canceled and unchanged
    old_sub = next(s for s in subscriptions if s.id == canceled_sub.id)
    assert old_sub.status == SubscriptionStatus.CANCELED

    assert user.pending_checkout is False


@pytest.mark.asyncio
async def test_upgrade_checkout_with_unknown_subscription_id_creates_new(
    db_session, test_settings
):
    """
    Req 3.6: Upgrade checkout where current_subscription_id references a
    subscription that doesn't exist locally — handler creates a new subscription.
    """
    user = await make_classic_user(db_session)
    user.pending_checkout = True
    await _make_pro_plan(db_session)
    await db_session.flush()

    checkout_session = _make_checkout_session(
        user_id=user.id,
        stripe_subscription_id=FAKE_STRIPE_SUB_ID_NEW,
        is_upgrade=True,
        current_subscription_id="sub_doesnt_exist",
    )

    stripe_sub_mock = _make_stripe_subscription_mock(
        stripe_id=FAKE_STRIPE_SUB_ID_NEW, status="active"
    )

    with patch.object(
        stripe.Subscription,
        "retrieve_async",
        new=AsyncMock(return_value=stripe_sub_mock),
    ):
        await billing_services.handle_checkout_session_completed(
            db_session, test_settings, checkout_session
        )

    result = await db_session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()
    assert subscription is not None
    assert subscription.stripe_subscription_id == FAKE_STRIPE_SUB_ID_NEW
    assert user.pending_checkout is False


@pytest.mark.asyncio
async def test_checkout_completed_unknown_user_returns_early(db_session, test_settings):
    """
    Req 3.6: Webhook referencing a non-existent user_id logs error and returns
    without raising.
    """
    await _make_pro_plan(db_session)

    checkout_session = _make_checkout_session(
        user_id=999999,  # does not exist
        is_upgrade=False,
    )

    # Should not raise
    await billing_services.handle_checkout_session_completed(
        db_session, test_settings, checkout_session
    )

    result = await db_session.execute(select(Subscription))
    subscriptions = result.scalars().all()
    assert len(subscriptions) == 0


@pytest.mark.asyncio
async def test_checkout_completed_missing_user_id_returns_early(
    db_session, test_settings
):
    """
    Req 3.6: Webhook with no user_id in metadata logs error and returns without raising.
    """
    checkout_session = MagicMock(spec=stripe.checkout.Session)
    checkout_session.client_reference_id = None
    checkout_session.metadata = {}  # no user_id
    checkout_session.subscription = FAKE_STRIPE_SUB_ID
    checkout_session.customer = FAKE_STRIPE_CUSTOMER_ID

    # Should not raise
    await billing_services.handle_checkout_session_completed(
        db_session, test_settings, checkout_session
    )


@pytest.mark.asyncio
async def test_standard_checkout_sets_stripe_customer_id(db_session, test_settings):
    """
    Req 3.1: When stripe_customer_id is not set on user, it should be populated
    from the checkout session.
    """
    user = await make_classic_user(db_session)
    assert user.stripe_customer_id is None
    await _make_pro_plan(db_session)

    checkout_session = _make_checkout_session(
        user_id=user.id,
        is_upgrade=False,
        customer_id=FAKE_STRIPE_CUSTOMER_ID,
    )

    stripe_sub_mock = _make_stripe_subscription_mock()

    with patch.object(
        stripe.Subscription,
        "retrieve_async",
        new=AsyncMock(return_value=stripe_sub_mock),
    ):
        await billing_services.handle_checkout_session_completed(
            db_session, test_settings, checkout_session
        )

    assert user.stripe_customer_id == FAKE_STRIPE_CUSTOMER_ID
