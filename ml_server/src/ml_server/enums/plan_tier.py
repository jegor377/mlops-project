import enum


class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    CUSTOM = "custom"
