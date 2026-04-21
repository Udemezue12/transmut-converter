

import logging
from datetime import datetime, timedelta, timezone

import httpx
from celery import shared_task

from core.get_db import SyncSessionLocal
from repos.auth_repo import AuthRepo

logger = logging.getLogger(__name__)


@shared_task(
    name="delete_blacklisted_tokens",
    autoretry_for=(httpx.HTTPError, ConnectionError, RuntimeError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def delete_blacklisted_tokens_tasks():
    try:
        with SyncSessionLocal() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            result = AuthRepo(db).sync_delete_expired_blacklisted_tokens(cutoff)
            logger.info("Blacklisted tokens cleanup completed.")
            return result
    except Exception:
        logger.exception("Failed to clean up blacklisted tokens")