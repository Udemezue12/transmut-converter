
from quart import Blueprint, request
from quart_schema import (
    tag,
)

from core.throttling import rate_limiter_manager
from services.service_media_service import ServeMediaService
from core.safe_handler import safe_handler

router = Blueprint("Download File", __name__, url_prefix="/api/v1")


class ServeMediaRoutes:
    @classmethod
    def register_route(cls, app):
        app.register_blueprint(router)

    @staticmethod
    @router.get("/media/converted/<filename>")
    @safe_handler
    @tag(["Download or Preview File"])
    @rate_limiter_manager.limit(times=6, seconds=15)
    async def serve_converted_file(filename: str):
        return await ServeMediaService().serve_converted_file(filename, request)

    @staticmethod
    @router.get("/media/preview/<filename>")
    @tag(["Download or Preview File"])
    @safe_handler
    @rate_limiter_manager.limit(times=6, seconds=10)
    async def preview_file(filename: str):
        return await ServeMediaService().preview_file(request, filename)
