from datetime import datetime
from pydantic import BaseModel

from src.ml_server.enums.plan_tier import PlanTier
from src.ml_server.models.subscription import SubscriptionStatus


class SubscriptionPlanOut(BaseModel):
    name: str
    tier: PlanTier
    price_cents: int | None

    model_config = {"from_attributes": True}


class SubscriptionOut(BaseModel):
    status: SubscriptionStatus
    current_period_start: datetime | None
    current_period_end: datetime | None
    plan: SubscriptionPlanOut | None
