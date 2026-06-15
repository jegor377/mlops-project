from pydantic import BaseModel


class RequestLogResponse(BaseModel):
    id: int
    method: str
    path: str
    status_code: int
    latency_ms: int
    ip: str | None
    created_at: str

    model_config = {"from_attributes": True}


class RequestLogPage(BaseModel):
    items: list[RequestLogResponse]
    total: int
    page: int
    size: int


class RequestStatsResponse(BaseModel):
    requests_today: int
    daily_limit: int
    requests_this_month: int
    avg_latency_ms: int | None
    error_rate: float | None   # 0.0–1.0
    spark: list[int]           # last 20 days, index 0 = oldest, index 19 = today
