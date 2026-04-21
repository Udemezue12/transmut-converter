import uuid

from quart import Blueprint, request
from quart_schema import tag, validate_response

from auth_utils.auth_role_permission import require_auth
from core.get_current_user import get_current_user
from core.get_db import get_db_async
from core.safe_handler import safe_handler
from core.throttling import rate_limiter_manager
from models.models import User
from schemas.schema import (
    UserFileConvertedUploadSchema
)
from services.converted_service import ConvertedFileService as ConvertedService

router = Blueprint("Converted File Uploads", __name__, url_prefix="/api/v1")


class ConvertedRoutes:
    @classmethod
    def register_route(cls, app):
        app.register_blueprint(router)

    @staticmethod
    @router.get("/converted/<converted_id>/file")
    @tag(["Converted File Uploads"])
    @safe_handler
    @rate_limiter_manager.limit(times=3, seconds=10)
    @validate_response(UserFileConvertedUploadSchema, 200)
    @require_auth
    async def get_user_converted(converted_id: str):
        current_user: User = await get_current_user(request)
        async with get_db_async() as db:
            return await ConvertedService(db).get_user_conversion(uuid.UUID(converted_id), current_user)

    @staticmethod
    @router.get("/converted/files")
    @tag(["Converted File Uploads"])
    @validate_response(list[UserFileConvertedUploadSchema], 200)
    @safe_handler
    @require_auth
    @rate_limiter_manager.limit(times=3, seconds=10)
    async def get_all_users_converted(page: int = 1, per_page: int = 20):
        current_user: User = await get_current_user(request)
        async with get_db_async() as db:
            return await ConvertedService(db).get_user_file_conversions(
                current_user, page, per_page
            )

    # @staticmethod
    # @router.delete("/uploaded/<upload_id>/delete")
    # @tag(["File Uploads"])
    # @safe_handler
    # @rate_limiter_manager.limit(times=3, seconds=10)
    # @require_auth
    # async def delete_user_upload(upload_id: uuid.UUID):
    #     current_user: User = await get_current_user(request)
    #     async with get_db_async() as db:
    #         return await UploadService(db).delete_upload(upload_id, current_user)
