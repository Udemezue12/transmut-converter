


import uuid
from pathlib import Path

import httpx
from celery import shared_task
from core.urrlib import sanitize_filename
from core.get_db import SyncSessionLocal
from core.media_settings import MEDIA_DIR
from core.redis_client import redis_client
from core.settings import settings
from models.enums import ConversionStatus, FileType, OutputFormat, TaskStatus
from repos.upload_repo import UploadRepo
from services.bytes_conversion_service import convert_bytes
from services.converted_service import ConvertedFileService
from utils.file_detection import get_mime_from_output_format

BASE_URL=settings.BASE_URL


@shared_task(
    name="convert_media",
    autoretry_for=(httpx.HTTPError, ConnectionError, RuntimeError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def convert_task(
    header_results=None,
    temp_file_id: str | None = None,
    temp_file_path: str | None = None,
    mime: str | None = None,
    file_type: str | None = None,
    output_format: str | None = None,
    filename: str | None = None,
) -> dict:

    if not all([mime, file_type,filename, temp_file_id, output_format, filename]):
     return {
        "message": "Missing required fields"
    }
    db = SyncSessionLocal()
    temp_path = Path(temp_file_path)

    try:
        upload_id = None

        if not temp_path.exists():
            raise FileNotFoundError(f"Temp file missing: {temp_file_path}")

        if header_results and isinstance(header_results, list):
            first_result = header_results[0]

            if isinstance(first_result, dict):
                upload_id = first_result.get("upload_id")
        print(f"[DEBUG] header_results={header_results}")
        print(f"[DEBUG] extracted upload_id={upload_id}")

        upload_uuid = uuid.UUID(upload_id) if upload_id else None

        file_bytes = temp_path.read_bytes()

        ft = FileType(file_type)
        output_fmt = OutputFormat(output_format)

        converted = convert_bytes(file_bytes, mime, ft, output_fmt)

        filename_no_ext = sanitize_filename(Path(filename).stem)
        final_filename = f"{filename_no_ext}.{output_fmt.value}"

        output_path = MEDIA_DIR / final_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(converted)

        temp_path.unlink(missing_ok=True)

        mime_type = get_mime_from_output_format(output_fmt)

        upload = None
        if upload_uuid:
            upload = UploadRepo(db).sync_get_upload_id(upload_uuid)

        if upload:
            ConvertedFileService(db).handle_converted_upload(
                output_format=output_fmt,
                file_path=output_path,
                resource_type=upload.cloudinary_file_resource_type,
                upload_id=upload.id,
                celery_task_id=str(convert_task.request.id),
                status=ConversionStatus.COMPLETED,
                error_message="No Error",
                original_filename=filename,

            )

        return {
            "status": TaskStatus.COMPLETED,
            "output_format": output_fmt.value,
            "filename": final_filename,
            "mime": mime_type,
            "download_url": f"{BASE_URL}/api/v1/media/converted/{final_filename}?mime_type={mime_type}",
            "view_url": f"{BASE_URL}/api/v1/media/preview/{final_filename}?mime_type={mime_type}"
        }

    except Exception as e:
        temp_path.unlink(missing_ok=True)
        raise Exception(str(e)) 

    finally:

        redis_client.sync_delete(f"upload_id:{temp_file_id}")
        db.close()
