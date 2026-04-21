import secrets

from quart import jsonify, session
from models.enums import ENVSettings

from core.settings import settings


def get_csrf_token():
    try:
        csrf_token = secrets.token_hex(32)

        response = jsonify({"csrf_token": csrf_token})
        session["csrf_token"] = csrf_token

        response.headers["Access-Control-Allow-Origin"] = settings.FRONTEND_URL
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Cache-Control"] = "no-store"

        if settings.ENV == ENVSettings.Production:
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,
                secure=True,
                samesite="lax",
                max_age=settings.CSRF_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                path="/"
            )
            return response

        else:
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,
                secure=False,
                samesite="lax",
                max_age=settings.CSRF_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                path="/"
            )
            return response

    except Exception as e:
        return jsonify(
            status_code=500,
            content={"detail": f"Failed to generate CSRF token: {str(e)}"},
        )
