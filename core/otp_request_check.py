from typing import Optional
from .redis_client import redis_client


class OTPRequestCheck:
    def __init__(self):
        self.async_redis = redis_client.async_client
        self.sync_redis = redis_client.sync_client
        self.OTP_COOLDOWN_SECONDS = 60
        self.MAX_REQUESTS_PER_HOUR = 5
        self.WINDOW_SECONDS = 3600

    def _normalize(self, email: str) -> str:
        return email.strip().lower()

    def _cooldown_key(self, email: str) -> str:
        return f"otp:cooldown:{email}"

    def _count_key(self, email: str) -> str:
        return f"otp:count:{email}"

    async def can_request_otp(self, email: str) -> bool:
        email = self._normalize(email)

        cooldown_key = self._cooldown_key(email)
        count_key = self._count_key(email)

        async with self.async_redis.pipeline(transaction=True) as pipe:
            pipe.exists(cooldown_key)
            pipe.get(count_key)
            cooldown_exists, current_count = await pipe.execute()

        cooldown_exists = bool(cooldown_exists)
        current_count = int(current_count) if current_count else 0

        if cooldown_exists:
            return False

        if current_count >= self.MAX_REQUESTS_PER_HOUR:
            return False

        return True

    def can_request_otp_sync(self, email: str) -> bool:
        email = self._normalize(email)

        cooldown_key = self._cooldown_key(email)
        count_key = self._count_key(email)

        with self.sync_redis.pipeline(transaction=True) as pipe:
            pipe.exists(cooldown_key)
            pipe.get(count_key)
            cooldown_exists, current_count = pipe.execute()

        cooldown_exists = bool(cooldown_exists)
        current_count = int(current_count) if current_count else 0

        if cooldown_exists:
            return False

        if current_count >= self.MAX_REQUESTS_PER_HOUR:
            return False

        return True

    async def record_otp_request(self, email: str):
        email = self._normalize(email)

        cooldown_key = self._cooldown_key(email)
        count_key = self._count_key(email)

        async with self.async_redis.pipeline(transaction=True) as pipe:
            pipe.set(cooldown_key, "1", ex=self.OTP_COOLDOWN_SECONDS)

            pipe.incr(count_key)
            pipe.expire(count_key, self.WINDOW_SECONDS, nx=True)

            await pipe.execute()

    async def get_retry_after(self, email: str) -> Optional[int]:
        email = self._normalize(email)

        ttl = await self.async_redis.ttl(self._cooldown_key(email))
        if ttl is None or ttl <= 0:
            return None
        return ttl
