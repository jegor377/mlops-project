from pydantic import BaseModel


class RequestStatsResponse(BaseModel):
    requests_today: int
    daily_limit: int
    requests_this_month: int
    avg_latency_ms: int | None
    latency_count: int
