import uuid

import httpx
from celery import shared_task

from core.get_db import SyncSessionLocal

from models.enums import FileType
from services.upload_service import UploadService


@shared_task(
    name="tasks_media_upload",
    autoretry_for=(httpx.HTTPError, ConnectionError, RuntimeError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def task_media(
    detected_mime: str,
    file_type: FileType,
    temp_file_id: str,
    user_id: str,
    original_filename: str
):
    try:
        db = SyncSessionLocal()
        user_uuid = uuid.UUID(user_id)

        result = UploadService(db).handle_upload(
            detected_mime=detected_mime,
            temp_file_id=temp_file_id,
            file_type=file_type,
            original_filename=original_filename,
            user_id=user_uuid,
        )
        upload_id = result.get("upload_id") if result else None

        print(f"[UPLOAD RESULT] extracted upload_id={upload_id}")
        if not upload_id:
            return {"detail":"Upload failed: upload_id is None"}
        return {
            "upload_id": str(upload_id),
            "temp_file_id": temp_file_id,
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()
