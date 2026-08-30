from src.ml_server.enums.plan_tier import PlanTier


def has_pending_checkout(plan: PlanTier) -> bool:
    return plan == PlanTier.PRO