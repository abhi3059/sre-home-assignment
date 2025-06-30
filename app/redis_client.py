import redis.asyncio as redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TTL = 300

async def connect_to_redis():
    return await redis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}",
        encoding="utf8",
        decode_responses=True
    )