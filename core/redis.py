import redis.asyncio as redis
from core.config import settings

REDIS_URL = settings.REDIS_URL
redis_client = redis.from_url(REDIS_URL)
