from datetime import datetime, timedelta, timezone


from quart import Request, abort, jsonify, session

from auth_utils.auth_cookie import (
    clear_auth_cookies,
    set_auth_access_token,
    set_auth_cookies,
)
from auth_utils.auth_jwt import (
    create_access_token,
    create_token_pair,
    decode_refresh_token,
)
from celery_worker.celery_app import app as task_app
from core.breaker import breaker
from core.redis_idempotency import RedisIdempotency
from core.settings import settings
from models.models import User
from repos.auth_repo import AuthRepo
from security.user_generate import user_generate
from security.user_verification import (
    UserVerification,
)
from middleware.csrf_middleware import validate_csrf
from core.otp_request_check import OTPRequestCheck
from core.hash_file import ComputeHash

ACCESS_EXPIRE_MINUTES = settings.ACCESS_EXPIRE_MINUTES
REFRESH_EXPIRE_DAYS = settings.REFRESH_EXPIRE_DAYS
SECURE_COOKIES = settings.SECURE_COOKIES
access_exp = datetime.now(timezone.utc) + timedelta(
    minutes=settings.ACCESS_EXPIRE_MINUTES
)

refresh_exp = datetime.now(timezone.utc) + \
    timedelta(days=settings.REFRESH_EXPIRE_DAYS)


class AuthService:
    REGISTER_LOCK_KEY = "register-auth-service-v2"
    VERIFY_EMAIL_KEY = "login-auth-service-v2"

    def __init__(self, db):
        self.repo: AuthRepo = AuthRepo(db)

        self.user_verification: UserVerification = UserVerification()
        self.otp_check = OTPRequestCheck()
        self.hash = ComputeHash()

        self.redis_idempotency: RedisIdempotency = RedisIdempotency(
            "auth-service-startup"
        )

    async def register(self, data):
        async def _handler():
            email = data.email.strip().lower()
            username = data.username.strip().lower()
            phone_number = data.phone_number.strip() if data.phone_number else None
            first_name = data.first_name.strip()
            last_name = data.last_name.strip()

            full_name = f"{first_name} {last_name}"

            email_hash = self.hash.hash_email(email)

            if await self.repo.get_by_email_hash(email_hash):
                abort(400, description="Email already registered")

            if await self.repo.get_by_username(username):
                abort(400, description="Username already taken")

            if phone_number and await self.repo.get_by_phoneNumber(phone_number):
                abort(400, description="Phone number already taken")

            if await self.repo.find_users_by_name_strict(full_name):
                abort(400, description="User with the same name already exists")

            user = User(
                username=username,
                email=email,
                email_hash=email_hash,
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                role=data.role,
                email_verified=False,
            )

            user.set_password(raw_password=data.password)

            await self.repo.create(user)

            otp = await user_generate.generate_otp(email)
            token = user_generate.generate_verify_token(email)

            task_app.send_task(
                "send_verify_email_notification",
                args=[
                    str(phone_number),
                    str(email),
                    str(otp),
                    str(user.full_name),
                    str(token),
                ],
            )

            return {
                "message": "Registration successful! Please verify your email.",
                "status": 201,
            }

        return await self.redis_idempotency.run_once(
            key=f"{self.REGISTER_LOCK_KEY}:{data.email}:{data.username}",
            coro=_handler,
            ttl=300,
        )

    async def login(self, data, request: Request):
        async def handler():
            await validate_csrf(request)
           
            user = await self.repo.get_by_email(data.email)
            if not user or not user.check_password(raw_password=data.password):
                raise ValueError("Invalid credentials")

            # if not user.email_verified:
            #     abort(
            #         code=403,
            #         description="Email not verified. Please verify your account to login.",
            #     )

            token_pair = create_token_pair(str(user.id))
            access_token = token_pair.access_token
            refresh_token = token_pair.refresh_token

            response = jsonify(
                {
                    "message": "Login successful",
                    "user": {
                        "id": str(user.id),
                        "fullname": str(user.full_name),
                        "username": user.username,
                        "role": user.role.name,
                    },
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
            )
            await self.repo.update_last_login(user)

            set_auth_cookies(response, access_token, refresh_token)
            return response

        return await breaker.call(handler)

    async def logout(self, request: Request):
        async def handler():
            access_token = (
                request.cookies.get("access_token")
                or request.headers.get("Authorization", "").split(" ", 1)[-1]
            )

            refresh_token = request.cookies.get("refresh_token")
            if access_token:
                await self.repo.blacklist_token(access_token)
            if refresh_token:
                await self.repo.blacklist_token(refresh_token)
            if hasattr(request, "session"):
                session.clear()
                request.session["logged_out"] = True
            response = jsonify({"message": "Logged out successfully"})
            clear_auth_cookies(response)
            return response

        return await breaker.call(handler)

    async def refresh(self, request: Request):
        raw_refresh = request.cookies.get("refresh_token")
        if not raw_refresh:
            return jsonify({"error": "No refresh token"}), 401

        if await self.repo.is_token_blacklisted(raw_refresh):
            return jsonify({"error": "Refresh token is blacklisted"}), 401

        try:
            payload = decode_refresh_token(raw_refresh)
        except Exception:
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        if payload.get("type") != "refresh":
            return jsonify({"error": "Wrong token type"}), 401

        new_access = create_access_token(
            user_id=payload["sub"],
        )

        response = jsonify({"message": "Token refreshed"})

        set_auth_access_token(response, new_access)
        return response

    async def resend_verification_email(self, email: str):
        async def handler():
            user = await self.repo.get_by_email(email)
            if user:
                if user.email_verified:
                    return {"message": "Email already verified."}

                allowed = await self.otp_check.can_request_otp(user.email)

                if allowed:
                    otp = user_generate.generate_otp(user.email)
                    token = await user_generate.generate_verify_token(user.email)

                    await self.otp_check.record_otp_request(user.email)

                    task_app.send_task(
                        "send_verify_email_notification",
                        args=[
                            str(user.phone_number),
                            str(user.email),
                            str(otp),
                            str(user.full_name),
                            str(token),
                        ],
                    )
            return {
                "message": "If the email exists, a verification message has been sent"
            }

        return await breaker.call(handler)

    async def resend_password_reset_link(self, email: str):
        async def handler():

            user = await self.repo.get_by_email(email)
            retry_after = None
            if user:
                allowed = await self.otp_check.can_request_otp(user.email)

                if allowed:
                    token = user_generate.generate_reset_token(user.email)
                    otp = await user_generate.generate_otp(user.email)

                    await self.otp_check.record_otp_request(user.email)

                    task_app.send_task(
                        "send_password_reset_notification",
                        args=[
                            str(user.phone_number),
                            str(user.email),
                            str(otp),
                            str(user.full_name),
                            str(token),
                        ],
                    )
                retry_after = await self.otp_check.get_retry_after(user.email)

            return {
                "message": "If the email exists, a reset link has been sent",
                "retry_after": retry_after
            }

        return await breaker.call(handler)

    async def verify_email(self, otp: str | None = None, token: str | None = None):
        async def handler():
            if bool(otp) == bool(token):
                abort(code=400, description="Provide either OTP or token, not both")
            if otp:
                email = await self.user_verification.verify_otp(otp)
            elif token:
                email = await self.user_verification.verify_reset_token(token)
            else:
                abort(code=400, description="No verification data provided")
            if not email:
                abort(code=400, description="Invalid or expired verification email")

            user = await self.repo.get_by_email(email)
            if not user:
                abort(code=404, description="Invalid or expired verification data")
            user.email_verified = True
            await self.repo.save(user)
            return {"Message": "Email verified successfully"}

        return await breaker.call(handler)

    async def forgot_password(self, payload):
        async def handler():
            user = await self.repo.get_by_email(payload.email)
            retry_after = None
            if user:
                allowed = await self.otp_check.can_request_otp(user.email)

                if allowed:
                    token = user_generate.generate_reset_token(user.email)
                    otp = await user_generate.generate_otp(user.email)

                    await self.otp_check.record_otp_request(user.email)

                    task_app.send_task(
                        "send_password_reset_notification",
                        args=[
                            str(user.phone_number),
                            str(user.email),
                            str(otp),
                            str(user.full_name),
                            str(token),
                        ],
                    )
                retry_after = await self.otp_check.get_retry_after(user.email)

            return {
                "message": "If the email exists, a reset link has been sent",
                "retry_after": retry_after
            }

        return await breaker.call(handler)

    async def reset_password(self, payload):

        email = None

        if payload.token and payload.token.strip():
            try:
                email = await self.user_verification.verify_reset_token(payload.token)
            except Exception:
                email = None

        if not email and payload.otp and payload.otp.strip():
            try:
                email = await self.user_verification.verify_otp(payload.otp)
            except Exception:
                email = None

        if not email:
            abort(code=400, description="Invalid or expired token")

        user = await self.repo.get_by_email(email)
        if not user:
            abort(code=404, description="Invalid or expired reset data")

        user.set_password(payload.new_password)
        await self.repo.update(user)

        return {"message": "Password reset successfully"}
