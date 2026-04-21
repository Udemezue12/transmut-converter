import logging

from redis.asyncio import Redis as aioredis
from redis.client import Redis as redis

from core.settings import settings

from .breaker import breaker

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        redis_url = settings.REDIS_URL

        if not redis_url:
            raise ValueError("Missing REDIS_URL in environment variables")

        self.redis_url = redis_url

        self.async_client = aioredis.from_url(
            self.redis_url,
            decode_responses=True,
        )

        self.sync_client = redis.from_url(
            self.redis_url,
            decode_responses=True,
        )

    async def async_setex(self, key: str, value: str, ttl: int = 3600):
        if key is None or value is None:
            raise ValueError("Cache key and value cannot be None")

        async def handler():
            try:
                await self.async_client.set(
                    str(key),
                    ttl,
                    value,
                )

            except Exception:
                raise

        await breaker.call(handler)

    def sync_setex(self, key: str, value: str, ttl: int = 3600) -> None:
        if key is None or value is None:
            raise ValueError("key and value cannot be None")

        try:
            self.sync_client.setex(str(key), ttl, value)
            print(f"[REDIS SET] key={key} value={value} ttl={ttl}")
            logger.debug("kEY set successfully for key: %s", key)

        except Exception as e:
            logger.error("Redis sync SET error", exc_info=e)

    async def async_get(self, key: str):
        try:
            return await self.async_client.get(str(key))

        except Exception as e:

            return None
    def sync_get(self, key: str):
        try:
            return self.sync_client.get(str(key))

        except Exception as e:

            return None

    async def async_delete(self, key: str) -> bool:
        try:
            result = await self.async_client.delete(str(key))
            return result > 0

        except Exception:
            return False
    def sync_delete(self, key: str) -> bool:
        try:
            result = self.sync_client.delete(str(key))
            return result > 0

        except Exception:
            return False


redis_client = RedisClient()
