from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


VALID_SCOPES = {
    "inference:basic",
}


class PATCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(min_length=1)
    expires_in_days: Optional[int] = Field(default=None, gt=0, le=365)

    def validate_scopes(self) -> list[str]:
        invalid = set(self.scopes) - VALID_SCOPES
        if invalid:
            raise ValueError(f"Invalid scopes: {invalid}")
        return list(set(self.scopes))  # deduplicate


class PATStatus(str, Enum):
    ALL = "all"
    ACTIVE = "active"
    EXPIRED = "expired"


class PATResponse(BaseModel):
    id: int
    name: str
    token_prefix: str
    scopes: list[str]
    expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, pat) -> "PATResponse":
        return cls(
            id=pat.id,
            name=pat.name,
            token_prefix=pat.token_prefix,
            scopes=pat.scopes.split(",") if pat.scopes else [],
            expires_at=pat.expires_at,
            created_at=pat.created_at,
            last_used_at=pat.last_used_at,
            is_active=pat.is_active,
        )


class PATPage(BaseModel):
    items: list[PATResponse]
    total: int
    page: int
    size: int


class PATCreateResponse(PATResponse):
    """Returned only at creation time — includes raw token."""
    raw_token: str
