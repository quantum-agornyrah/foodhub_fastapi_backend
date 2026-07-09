import redis.asyncio as aioredis
from src.utils.settings import settings

# Create a shared, reusable asynchronous Redis client
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)