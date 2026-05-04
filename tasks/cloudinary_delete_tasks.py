

import httpx
from celery import shared_task

from core.cloudinary_setup import cloudinary_service


@shared_task(
    name="tasks_delete_cloudinary_file",
    autoretry_for=(httpx.HTTPError, ConnectionError, RuntimeError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def delete_cloudinary_file(public_id: str, resource_type: str):
    try:
        cloudinary_service.delete_file(public_id, resource_type)
        print(
            f"Successfully deleted file with public_id={public_id} and resource_type={resource_type}")
        return {
            "message": "File deleted successfully",
            "public_id": public_id,
            "resource_type": resource_type
        }
    except Exception as e:
        print(
            f"Error deleting file with public_id={public_id} and resource_type={resource_type}: {e}")
        return{
            "message": "Failed to delete file",
            "public_id": public_id,
            "resource_type": resource_type,
            "error": str(e)

        }