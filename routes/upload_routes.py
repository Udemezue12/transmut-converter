import uuid

from quart import Blueprint, request
from quart_schema import tag, validate_request, validate_response

from auth_utils.auth_role_permission import require_auth
from core.cloudinary_setup import cloudinary_service as cloudinary_client
from core.get_current_user import get_current_user
from core.get_db import get_db_async
from core.safe_handler import safe_handler
from core.throttling import rate_limiter_manager
from models.models import User
from schemas.schema import UploadDeleteRequest, UserFileUploadSchema
from services.upload_service import UploadService 

router = Blueprint("Original File Uploads", __name__, url_prefix="/api/v1")


class UploadRoutes:
    @classmethod
    def register_route(cls, app):
        app.register_blueprint(router)

    @staticmethod
    @router.get("/uploaded/<upload_id>/file")
    @tag(["Original File Uploads"])
    @safe_handler
    @rate_limiter_manager.limit(times=3, seconds=10)
    @validate_response(UserFileUploadSchema, 200)
    @require_auth
    async def get_user_upload(upload_id: str):
        current_user: User = await get_current_user(request)
        async with get_db_async() as db:
            return await UploadService(db).get_user_upload(uuid.UUID(upload_id), current_user)
   

    @staticmethod
    @router.get("/uploaded/files")
    @tag(["Original File Uploads"])
    @validate_response(list[UserFileUploadSchema], 200)
    @safe_handler
    @require_auth
    @rate_limiter_manager.limit(times=3, seconds=10)
    async def get_user_uploads(page: int = 1, per_page: int = 20):
        current_user: User = await get_current_user(request)
        async with get_db_async() as db:
            return await UploadService(db).get_user_uploads(
                current_user, page, per_page
            )

    @staticmethod
    @router.delete("/uploaded/<upload_id>/delete")
    @tag(["Original File Uploads"])
    @safe_handler
    @rate_limiter_manager.limit(times=3, seconds=10)
    @require_auth
    async def delete_user_upload(upload_id: str):
        current_user: User = await get_current_user(request)
        async with get_db_async() as db:
            return await UploadService(db).delete_upload(uuid.UUID(upload_id), current_user)

  

    @staticmethod
    @router.post("/cloudinary/delete/multiple")
    @tag(["Cloudinary File Uploads"])
    @validate_request(UploadDeleteRequest)
    @safe_handler
    async def delete_multiple(
        data: UploadDeleteRequest,
    ):
        return await cloudinary_client.delete_resources(
            public_ids=data.public_ids,
        )

    @staticmethod
    @router.get("/cloudinary/resources")
    @tag(["Cloudinary File Uploads"])
    @safe_handler
    async def list_cloudinary_resources(
        folder: str | None = None,
        max_results: int = 50,
        next_cursor: str | None = None,
        # current_user: User = Depends(require_admin_user),
    ):
        return await cloudinary_client.list_resources(
            request=request,
            folder=folder,
            max_results=max_results,
            next_cursor=next_cursor,
        )
