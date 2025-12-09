import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

async def get_cache(key: str):
    return await redis_client.get(key)

async def set_cache(key: str, value: str, expire: int = 60):
    await redis_client.set(key, value, ex=expire)
