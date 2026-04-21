import hashlib
import hmac
import re
import secrets
import uuid
from random import randint

from itsdangerous import URLSafeTimedSerializer
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
    raise ValueError("REDIS_URL must be configured")
reset_serializer = URLSafeTimedSerializer(RESET_SECRET_KEY)
verify_serializer = URLSafeTimedSerializer(VERIFY_EMAIL_SECRET_KEY)

redis = Redis.from_url(REDIS_URL, decode_responses=True)


class UserGenerate:
    
    def sync_generate_reference(self):
        return str(uuid.uuid4().int)[:12]
   



    def generate_secure_cloudinary_public_id(self,prefix: str = "uploads") -> str:
     return f"{prefix}/{uuid.uuid4().hex}_{secrets.token_hex(8)}"
    def generate_unique_idem_key(
        self,
        request
    ) -> str:
        key = request.headers.get("Idempotency-Key")
        return key or str(uuid.uuid4())

    def hmac_sha256(self, value: str, secret: str) -> str:
        return (
            hmac.new(
                key=secret.encode(),
                msg=value.encode(),
                digestmod=hashlib.sha256,
            )
            .hexdigest()
            .upper()
        )

    def generate_secure_public_id(
        self,
        prefix: str | None = None,
        length: int = 32,
    ):
        token = uuid.uuid4().hex[:length]

        token = re.sub(r"[^a-z0-9_-]", "_", token)

        if prefix:
            prefix = re.sub(r"[^a-z0-9_-]", "_", prefix.lower().strip("_"))
            return f"{prefix}_{token}"

        return token

    def delete_token(self) -> str:
        return secrets.token_hex(32)

    def generate_verify_token(self, email: str) -> str:
        return verify_serializer.dumps(email, salt=settings.VERIFY_EMAIL_SALT)

    def generate_reset_token(self, email: str) -> str:
        return reset_serializer.dumps(email, salt=settings.RESET_PASSWORD_SALT)

    async def generate_otp(self, email: str) -> str:
        async def handler():
            otp = str(randint(100000, 999999))
            await redis.setex(f"otp:{email}", 300, otp)
            return otp

        return await breaker.call(handler)


user_generate = UserGenerate()