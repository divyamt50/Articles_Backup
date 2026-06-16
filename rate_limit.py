import os
from redis import asyncio as aioredis
from fastapi import HTTPException


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses = True)

TIER_LIMIT = {"free":5, "pro":60}
TIME_SECONDS = 60

async def limit_check(user_id:int, tier:str)->None:
    key = f"{user_id}:request_num"

    time_total = TIME_SECONDS
    max_reqs = TIER_LIMIT.get(tier, TIER_LIMIT["free"])

    curr_val = await redis_client.incr(key)

    if curr_val == 1:
        await redis_client.expire(key, time_total)

    if curr_val > max_reqs:
        ttl = await redis_client.ttl(key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded, please try in {ttl} seconds"
        )