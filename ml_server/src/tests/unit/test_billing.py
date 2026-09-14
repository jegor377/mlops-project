# Property 1: Plan Seeding Idempotence
# Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5

import pytest
from sqlalchemy import select
from src.ml_server.models.plan import Plan
from src.ml_server.enums.plan_tier import PlanTier


@pytest.mark.asyncio
async def test_seed_default_plans_idempotence(db_session, test_settings):
    """
    Property 1: Plan Seeding Idempotence
    
    For any startup sequence, running the seed default plans mechanism multiple times
    SHALL result in exactly one Free plan and one Pro plan existing in the database
    with the correct tier values.
    
    This test verifies that running seed_default_plans() N times produces exactly
    1 Free + 1 Pro plan.
    """
    from src.ml_server.services.billing import seed_default_plans
    
    # Run seed_default_plans() multiple times to test idempotence
    for _ in range(5):
        await seed_default_plans(db_session, test_settings)
    
    # Query all plans
    result = await db_session.execute(select(Plan))
    plans = result.scalars().all()
    
    # Verify exactly 2 plans exist (Free + Pro)
    assert len(plans) == 2, f"Expected 2 plans, got {len(plans)}"
    
    # Verify Free plan exists with correct tier
    free_plan = next((p for p in plans if p.tier == PlanTier.FREE), None)
    assert free_plan is not None, "Free plan not found"
    assert free_plan.name == "Free"
    assert free_plan.price_cents == 0
    assert free_plan.stripe_price_id is None
    assert free_plan.requests_per_day is None  # unlimited
    assert free_plan.api_key_limit is None  # unlimited
    assert free_plan.history_days is None  # unlimited
    assert free_plan.priority_support is False
    assert free_plan.webhook_notifications is False
    assert free_plan.dedicated_support is False
    assert free_plan.custom_sla is False
    assert free_plan.on_prem is False
    assert free_plan.is_active is True
    
    # Verify Pro plan exists with correct tier
    pro_plan = next((p for p in plans if p.tier == PlanTier.PRO), None)
    assert pro_plan is not None, "Pro plan not found"
    assert pro_plan.name == "Pro"
    assert pro_plan.price_cents is None  # negotiated via Stripe
    assert pro_plan.stripe_price_id == test_settings.stripe.price_id.get_secret_value()
    assert pro_plan.requests_per_day is None  # unlimited
    assert pro_plan.api_key_limit is None  # unlimited
    assert pro_plan.history_days is None  # unlimited
    assert pro_plan.priority_support is True
    assert pro_plan.webhook_notifications is True
    assert pro_plan.dedicated_support is False
    assert pro_plan.custom_sla is False
    assert pro_plan.on_prem is False
    assert pro_plan.is_active is True
