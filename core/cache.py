import asyncio
import base64
import json
import logging
from typing import Any, Optional

import redis

import redis.asyncio as aioredis
from tenacity import retry, stop_after_attempt, wait_exponential

from .breaker import breaker
from .settings import settings

logger = logging.getLogger(__name__)


class Cache:
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

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def connect(self):
        async def handler():
            try:
                logger.info("Connecting to Redis...")
                pong = await self.async_client.ping()

                if pong:
                    logger.info("Connected to Redis.")
                else:
                    raise ConnectionError("Redis ping failed.")

            except Exception as e:
                logger.error("Redis connection error", exc_info=e)
                raise

        await breaker.call(handler)

    async def get(self, key: str) -> Optional[str]:
       
            try:
                value = await self.async_client.get(str(key))
                return value

            except Exception as e:
                logger.error("Redis GET error", exc_info=e)
                return None

        

    def sync_get(self, key: str) -> Optional[str]:
        try:
            return self.sync_client.get(str(key))

        except Exception as e:
            logger.error("Redis sync GET error", exc_info=e)
            return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        if key is None or value is None:
            raise ValueError("Cache key and value cannot be None")

        async def handler():
            try:
                await self.async_client.set(
                    str(key),
                    value,
                    ex=ttl,
                )
                logger.debug("Cache set successfully for key: %s", key)

            except Exception as e:
                logger.error("Redis SET error", exc_info=e)

        await breaker.call(handler)

    def sync_set(self, key: str, value: str, ttl: int = 3600) -> None:
        if key is None or value is None:
            raise ValueError("Cache key and value cannot be None")

        try:
            self.sync_client.set(
                str(key),
                value,
                ex=ttl,
            )
            logger.debug("Cache set successfully for key: %s", key)

        except Exception as e:
            logger.error("Redis sync SET error", exc_info=e)

    async def delete(self, key: str) -> bool:
        async def handler():
            try:
                result = await self.async_client.delete(str(key))
                return result > 0

            except Exception as e:
                logger.error("Redis DELETE error", exc_info=e)
                return False

        return await breaker.call(handler)

    def sync_delete(self, key: str) -> bool:
        try:
            result = self.sync_client.delete(str(key))
            return result > 0

        except Exception as e:
            logger.error("Redis sync DELETE error", exc_info=e)
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        data = await self.get(key)

        if not data:
            return None

        try:
            return json.loads(data)

        except json.JSONDecodeError:
            logger.error("Invalid JSON format in key: %s", key)
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 3600) -> None:
        logger.debug("Setting JSON cache for key: %s", key)
        data = json.dumps(value)
        await self.set(key, data, ttl)

    def set_json_sync(self, key: str, value: Any, ttl: int = 3600):
        loop = asyncio.get_event_loop()

        if loop.is_running():
            asyncio.create_task(self.set_json(key, value, ttl))
        else:
            loop.run_until_complete(self.set_json(key, value, ttl))

    async def delete_cache_keys_async(self, *keys: str):
        if not keys:
            return

        unique_keys = set(keys)

        await asyncio.gather(
            *(self.delete(key) for key in unique_keys)
        )

    def delete_cache_keys_sync(self, *keys: str):
        if not keys:
            return

        unique_keys = set(keys)

        for key in unique_keys:
            self.sync_delete(key)

    async def get_raw(self, key: str) -> Optional[bytes]:
        data = await self.get(key)

        if not data:
            return None

        try:
            return base64.urlsafe_b64decode(data.encode("utf-8"))

        except Exception as e:
            logger.error(
                "Failed to decode raw cache value for key %s",
                key,
                exc_info=e,
            )
            return None

    async def set_raw(self, key: str, value: bytes, ttl: int = 3600):
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("set_raw expects bytes")

        encoded = base64.urlsafe_b64encode(value).decode("ascii")

        await self.set(key, encoded, ttl)

        return {
            "key": key,
            "ttl": ttl,
            "size": len(encoded),
            "type": type(value).__name__,
        }

    async def delete_raw(self, key: str) -> bool:
        return await self.delete(key)

    async def ping(self) -> bool:
        try:
            return await self.async_client.ping()

        except Exception as e:
            logger.error("Redis ping failed", exc_info=e)
            return False


cache = Cache()