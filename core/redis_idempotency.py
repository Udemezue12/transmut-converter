import logging
from typing import Any, Awaitable, Callable

import redis.asyncio as aioredis
import redis
from .breaker import breaker
from .settings import settings

logger = logging.getLogger(__name__)


class RedisIdempotency:
    def __init__(self, namespace: str = "idempotency"):
        redis_url = settings.REDIS_URL

        if not redis_url:
            raise ValueError("Missing REDIS_URL in environment variables")

        self.namespace = namespace
        self.async_client = aioredis.from_url(
            redis_url,
            decode_responses=True,
        )
        self.sync_client = redis.from_url(
            redis_url,
            decode_responses=True,
        )

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def acquire(self, key: str, ttl: int) -> bool:
        async def handler():
            redis_key = self._key(key)

            result = await self.async_client.set(
                redis_key,
                "locked",
                ex=ttl,
                nx=True,
            )

            return result is True

        return await breaker.call(handler)

    def sync_acquire(self, key: str, ttl: int) -> bool:

        redis_key = self._key(key)

        result = self.sync_client.set(
            redis_key,
            "locked",
            ex=ttl,
            nx=True,
        )

        return result is True

    async def delete(self, key: str) -> bool:
        async def handler():
            redis_key = self._key(key)
            result = await self.async_client.delete(redis_key)
            return result > 0

        return await breaker.call(handler)

    def sync_delete(self, key: str) -> bool:

        redis_key = self._key(key)
        result = self.sync_client.delete(redis_key)
        return result > 0

    async def run_once(
        self,
        key: str,
        coro: Callable[[], Awaitable],
        ttl: int = 30,
    ):
        acquired = False

        try:
            acquired = await self.acquire(key, ttl)

            if not acquired:
                raise RuntimeError(
                    "Duplicate request in progress or already processed"
                )

            return await coro()

        finally:
            if acquired:
                try:
                    await self.delete(key)
                except Exception as e:
                    logger.warning(
                        f"Failed to delete idempotency key {key}: {e}")

    def sync_run_once(
        self,
        key: str,
        coro: Callable[[], Any],
        ttl: int = 30,
    ):
        acquired = False

        try:
            acquired = self.sync_acquire(key, ttl)

            if not acquired:
                raise RuntimeError(
                    "Duplicate request in progress or already processed"
                )

            return coro()

        finally:
            if acquired:
                try:
                    self.sync_delete(key)
                except Exception as e:
                    logger.warning(
                        f"Failed to delete idempotency key {key}: {e}")
