from contextlib import asynccontextmanager
from contextlib import contextmanager as synccontextmanager

from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.engine import Engine as SyncEngine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as SyncSession
from sqlalchemy.orm import sessionmaker as sync_sessionmaker

from .settings import settings

ASYNC_DATABASE_URL = settings.ASYNC_DATABASE_URL
SYNC_DATABASE_URL = settings.SYNC_DATABASE_URL

if not ASYNC_DATABASE_URL:
    raise ValueError("ASYNC_DATABASE_URL is not set in settings")
if not SYNC_DATABASE_URL:
    raise ValueError("SYNC_DATABASE_URL is not set in settings")

async_engine: AsyncEngine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
sync_engine: SyncEngine = create_sync_engine(
    SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
SyncSessionLocal = sync_sessionmaker(
    bind=sync_engine,
    class_=SyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@synccontextmanager
def get_db_sync() -> SyncSession:
    session = SyncSessionLocal()
    try:
        yield session
    except Exception:
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_db_async() -> AsyncSession:
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        raise
    finally:
        await session.close()


Base = declarative_base()
