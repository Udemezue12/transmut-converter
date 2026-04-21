from quart import Blueprint, request
from quart_schema import tag, validate_request

from auth_utils.auth_role_permission import require_auth
from core.get_db import get_db_async
from core.safe_handler import safe_handler
from core.throttling import rate_limiter_manager
from schemas.schema import EmailInput, ResetPassword, UserCreate, UserLogin, VerifyEmail
from services.auth_service import AuthService

router = Blueprint("Authentication", __name__, url_prefix="/api/v1/auth")


class AuthRoutes:
    @classmethod
    def register_route(cls, app):
        app.register_blueprint(router)

    @staticmethod
    @router.get("/me")
    @tag(["Authentication"])
    @safe_handler
    @rate_limiter_manager.limit(times=5, seconds=10)
    @require_auth
    async def get_current_user():
        return {"authenticated": True}

    @staticmethod
    @router.post("/register")
    @tag(["Authentication"])
    @safe_handler
    @rate_limiter_manager.limit(times=5, seconds=10)
    @validate_request(UserCreate)
    async def register(data: UserCreate):
        async with get_db_async() as db:
            return await AuthService(db).register(data)

    @staticmethod
    @router.post("/login")
    @tag(["Authentication"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    @validate_request(UserLogin)
    async def login(data: UserLogin):
        async with get_db_async() as db:
            return await AuthService(db).login(data, request)

    @staticmethod
    @router.post("/logout")
    @tag(["Authentication"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    @require_auth
    async def logout():
        async with get_db_async() as db:
            return await AuthService(db).logout(request)

    @staticmethod
    @router.post("/verify-email")
    @tag(["Authentication"])
    @validate_request(VerifyEmail)
    async def verify_email(data: VerifyEmail):
        async with get_db_async() as db:
            return await AuthService(db).verify_email(otp=data.otp, token=data.token)

    @staticmethod
    @router.post("/refresh")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Authentication"])
    @require_auth
    async def refresh():
        async with get_db_async() as db:
            return await AuthService(db).refresh(request=request)

    @staticmethod
    @router.post("/resend_verification_email")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Authentication"])
    @validate_request(EmailInput)
    async def resend_verification_email(data: EmailInput):
        async with get_db_async() as db:
            return await AuthService(db).resend_verification_email(email=data.email)

    @staticmethod
    @router.post("/resend_password_reset_link")
    @rate_limiter_manager.limit(times=5, seconds=10)
    @tag(["Authentication"])
    @validate_request(EmailInput)
    async def resend_password_reset_link(data: EmailInput):
        async with get_db_async() as db:
            return await AuthService(db).resend_password_reset_link(email=data.email)

    @staticmethod
    @router.post("/forgot_password")
    @tag(["Authentication"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    @validate_request(EmailInput)
    async def forgot_password(data: EmailInput):
        async with get_db_async() as db:
            return await AuthService(db).forgot_password(payload=data)

    @staticmethod
    @router.post("/reset_password")
    @tag(["Authentication"])
    @rate_limiter_manager.limit(times=5, seconds=10)
    @validate_request(ResetPassword)
    async def reset_password(data: ResetPassword):
        async with get_db_async() as db:
            return await AuthService(db).reset_password(payload=data)
