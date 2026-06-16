from redis import asyncio as aioredis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses = True)



async def cache_get(key:str) -> str|None:
    return await redis_client.get(key)  

async def cache_set(key:str, val:str, ttl:int) -> str|None:
    return await redis_client.set(key, val, ex=ttl)

async def cache_delete(key:str)->None:
    await redis_client.delete(key)