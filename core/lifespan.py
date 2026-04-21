from contextlib import asynccontextmanager
from .throttling import rate_limiter_manager


class LifespanService:
    def __init__(self, app):
        self.app = app
        self.app.before_serving(self.startup)
        self.app.after_serving(self.shutdown)

    @asynccontextmanager
    async def lifespan(self):
        try:
            await rate_limiter_manager.connect()
            print("Rate limiter initialized successfully.")
        except Exception as e:
            print(f"Rate limiter initialization failed: {e}")
            rate_limiter_manager.redis = None

        yield

        try:
            if rate_limiter_manager.redis:
                await rate_limiter_manager.redis.aclose()
            print("Rate limiter shutdown complete.")
        except Exception as e:
            print(f"Error during Rate limiter shutdown: {e}")

    async def startup(self):
        self.app._lifespan = self.lifespan()
        await self.app._lifespan.__aenter__()

    async def shutdown(self):
        await self.app._lifespan.__aexit__(None, None, None)