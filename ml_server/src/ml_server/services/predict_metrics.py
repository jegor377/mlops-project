from redis.asyncio import Redis
import logging

from src.ml_server.dependencies.rate_limit import first_day_of_next_month



logger = logging.getLogger(__name__)


async def record_req_metrics(
    redis: Redis,
    user_id: int,
    latency_ms: int,
) -> None:
    pipe = redis.pipeline()
    
    latency_sum_key = f"ls:{user_id}"
    pipe.incrbyfloat(latency_sum_key, latency_ms)
    pipe.expireat(latency_sum_key, first_day_of_next_month())
    
    latency_count_key = f"lc:{user_id}"
    pipe.incr(latency_count_key)
    pipe.expireat(latency_count_key, first_day_of_next_month())
    
    await pipe.execute()
