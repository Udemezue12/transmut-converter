import time
from pathlib import Path
from celery import shared_task
import httpx

from core.media_settings import MEDIA_DIR, TEMP_DIR


@shared_task(
    name="cleanup_old_converted_files",
    autoretry_for=(httpx.HTTPError, ConnectionError, RuntimeError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def cleanup_old_files_tasks(max_age_seconds: int = 3600):
    now = time.time()

    dirs_to_clean = [
        Path(MEDIA_DIR),
        Path(TEMP_DIR),
    ]

    for base_path in dirs_to_clean:
        print(f"[CLEANUP] Scanning: {base_path}")

        if not base_path.exists():
            print(f"[CLEANUP] Directory does not exist: {base_path}")
            continue

        deleted = 0
        failed = 0

        for file in base_path.rglob("*"):
            if file.is_file():
                try:
                    age = now - file.stat().st_mtime
                    if age > max_age_seconds:
                        file.unlink()
                        deleted += 1
                        print(f"[CLEANUP] Deleted: {file}")
                except Exception as e:
                    failed += 1
                    print(f"[CLEANUP] Failed to delete {file}: {e}")

        print(f"[CLEANUP] {base_path.name} — deleted: {deleted}, failed: {failed}")