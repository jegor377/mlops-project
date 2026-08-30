from pydantic import BaseModel, EmailStr, NameEmail, field_validator, Field

from src.ml_server.enums.plan_tier import PlanTier


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    subscription_plan: PlanTier = Field(alias="subscriptionPlan")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 72:
            raise ValueError("Password must be at most 72 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class Me(BaseModel):
    email: str
    id: int
    is_active: bool
    pending_checkout: bool


class Recipient(BaseModel):
    email: NameEmail
