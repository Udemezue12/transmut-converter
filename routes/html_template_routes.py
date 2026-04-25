from quart import Blueprint, render_template
from quart_schema import tag

from core.throttling import rate_limiter_manager

router = Blueprint("Templates", __name__,)


class TemplatesRoutes:
    @classmethod
    def register_route(cls, app):
        app.register_blueprint(router)

    @staticmethod
    @router.get("/")
    @tag(["Templates"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def index():
        return await render_template("upload.html")

    @staticmethod
    @router.get("/dashboard")
    @tag(["Templates"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def dashboard():
        return await render_template("dashboard.html")

    @staticmethod
    @router.get("/download")
    @tag(["Templates"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def download():
        return await render_template("download.html")

    @staticmethod
    @router.get("/trans/register")
    @tag(["Templates"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    async def register():
        return await render_template("register.html")

    @staticmethod
    @router.get("/trans/login")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Templates"])
    async def login():
        return await render_template("login.html")

    @staticmethod
    @router.get("/trans/verify-email")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Templates"])
    async def verify_email():
        return await render_template("verify_email.html")

    @staticmethod
    @router.get("/trans/forgot-password")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Templates"])
    async def forgot_password():
        return await render_template("forgot_password.html")

    @staticmethod
    @router.get("/trans/reset-password")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Templates"])
    async def reset_password():
        return await render_template("reset_password.html")

    @staticmethod
    @router.get("/files")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Templates"])
    async def files():
        return await render_template("files_dashboard.html")

    @staticmethod
    @router.get("/converted/<converted_id>")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Templates"])
    async def converted_file(converted_id: str):
        return await render_template("file_detail.html")
    @staticmethod
    @router.get("/uploaded/<upload_id>")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Templates"])
    async def uploaded_file(upload_id: str):
        return await render_template("file_detail.html")
