
import time

from functools import wraps
import inspect
from quart import Request, jsonify, request
from redis.asyncio import from_url

from .settings import settings


class RateLimitManager:
    def __init__(self):
        self.redis = None

    async def connect(self):
        try:
            self.redis = from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis.ping()
            print("Rate limiter connected to Redis successfully.")
        except Exception as e:
            print(f"Rate limiter initialization failed: {e}")
            self.redis = None

    async def _get_identifier(self, req: Request) -> str:
        try:
            user = getattr(req, "user", None) or getattr(req, "_user", None)
            user_id = getattr(user, "id", None)
            if user_id is not None:
                return f"user:{user_id}"
        except Exception:
            pass
        try:
            if req.remote_addr:
                return f"ip:{req.remote_addr}"
        except Exception:
            pass
        return "anonymous"

    async def is_rate_limited(self, key: str, times: int, seconds: int) -> bool:

        if self.redis is None:
            return False

        redis_key = f"rate_limit:{key}"
        try:
            pipe = self.redis.pipeline()
            now = time.time()
            window_start = now - seconds

            await pipe.zremrangebyscore(redis_key, "-inf", window_start)
            await pipe.zadd(redis_key, {str(now): now})
            await pipe.zcard(redis_key)
            await pipe.expire(redis_key, seconds)
            results = await pipe.execute()

            request_count = results[2]
            return request_count > times
        except Exception as e:
            print(f"Rate limit check failed: {e}")
            return False  # fail open

    def limit(self, times: int = 3, seconds: int = 10):

        def decorator(f):
            @wraps(f)
            async def wrapped(*args, **kwargs):
                identifier = await self._get_identifier(request)
                key = f"{f.__name__}:{identifier}"

                if await self.is_rate_limited(key, times, seconds):
                    return jsonify({
                        "detail": "Rate limit exceeded. Please try again later."
                    }), 429

                result = f(*args, **kwargs)

                if inspect.isawaitable(result):
                    result = await result

                return result

            return wrapped
        return decorator


rate_limiter_manager = RateLimitManager()
