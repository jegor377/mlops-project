from pydantic import BaseModel


class AuditLogEntryResponse(BaseModel):
    id: int
    event: str
    ip: str | None
    user_agent: str | None
    metadata: dict[str, str] | None
    created_at: str  # ISO 8601

    model_config = {"from_attributes": True}


class AuditLogPageResponse(BaseModel):
    items: list[AuditLogEntryResponse]
    total: int
    page: int
    size: int
