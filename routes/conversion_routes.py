from quart import Blueprint, request
from quart_schema import (
    tag,
    validate_request,
    
)

from core.get_current_user import get_current_user
from core.throttling import rate_limiter_manager
from models.models import User
from schemas.schema import ConvertRequest
from core.safe_handler import safe_handler
from services.conversion_service import ConversionService


router = Blueprint("Conversions", __name__, url_prefix="/api/v1")


class ConversionRoutes:
    @classmethod
    def register_route(cls, app):
        app.register_blueprint(router)

    @staticmethod
    @router.post("/detect/file")
    @tag(["Conversions"])
    @safe_handler
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def detect_file():
        current_user: User = await get_current_user(request)
        return await ConversionService().detect_file(request, current_user)

    @staticmethod
    @router.post("/detect/files")
    @tag(["Conversions"])
    @safe_handler
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def detect_files():
        current_user: User = await get_current_user(request)
        return await ConversionService().detect_files(request, current_user)

    @staticmethod
    @router.post("/start/conversion")
    @tag(["Conversions"])
    @safe_handler
    @validate_request(ConvertRequest)
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def start_conversion(data: ConvertRequest):
        current_user: User = await get_current_user(request)
        return await ConversionService().start_conversion(current_user,data)

    @staticmethod
    @router.get("/result/<task_id>")
    @tag(["Conversions"])
    @safe_handler
    @rate_limiter_manager.limit(times=8, seconds=11)
    async def get_result(task_id: str):
        return await ConversionService().get_result(task_id)

    @staticmethod
    @router.get("/download/<task_id>")
    @tag(["Conversions"])
    @safe_handler
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def download(task_id: str):
        return await ConversionService().download(task_id)
