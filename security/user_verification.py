from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from redis.asyncio import Redis
from core.breaker import breaker
from core.settings import settings


REDIS_URL = settings.REDIS_URL
RESET_PASSWORD_SALT = settings.RESET_PASSWORD_SALT
RESET_SECRET_KEY = settings.RESET_SECRET_KEY
VERIFY_EMAIL_SALT = settings.VERIFY_EMAIL_SALT
VERIFY_EMAIL_SECRET_KEY = settings.VERIFY_EMAIL_SECRET_KEY
if not RESET_SECRET_KEY or not VERIFY_EMAIL_SECRET_KEY:
    raise ValueError(
        "RESET_SECRET_KEY and VERIFY_EMAIL_SECRET_KEY must be configured")
if not REDIS_URL:
    raise ValueError("REDIS_URL be configured")
reset_serializer = URLSafeTimedSerializer(RESET_SECRET_KEY or "")
verify_serializer = URLSafeTimedSerializer(VERIFY_EMAIL_SECRET_KEY or "")
resend_tracker: dict[str, dict] = {}
redis = Redis.from_url(REDIS_URL, decode_responses=True)


class UserVerification:
    async def verify_reset_token(
        self, token: str, expiration: int = 3600
    ) -> str | None:
        try:
            email = reset_serializer.loads(
                token, salt=settings.RESET_PASSWORD_SALT, max_age=expiration
            )
            return email
        except (SignatureExpired, BadSignature):
            return None

    async def verify_verify_token(
        self, token: str, expiration: int = 3600
    ) -> str | None:
        try:
            email = verify_serializer.loads(
                token, salt=settings.VERIFY_EMAIL_SALT, max_age=expiration
            )
            return email
        except (SignatureExpired, BadSignature):
            return None

    async def verify_otp(self, otp: str) -> str:
        async def handler():
            async for key in redis.scan_iter(match="otp:*"):
                stored = await redis.get(key)
                if stored == otp:
                    await redis.delete(key)
                    return key.split(":")[1]
            return None

        return await breaker.call(handler)


user_verify = UserVerification()
