from functools import wraps

from quart import g, jsonify, request

from core.get_current_user import get_current_user
from models.enums import AdminRole
from models.models import User

from .auth_cookie_middleware import CookieJWTAuthentication


async def _authenticate() -> tuple[dict | None, str | None]:

    try:
        payload = await CookieJWTAuthentication().authenticate()
    except ValueError as exc:
        return None, str(exc)

    if payload is None:
        return None, "Authentication required"

    return payload, None


def _populate_g(payload: dict) -> None:

    g.current_user = payload
    g.current_user_id = payload.get("sub")
    


def require_auth(f):

    @wraps(f)
    async def wrapper(*args, **kwargs):
        payload, error = await _authenticate()
        if error or payload is None:
            return jsonify({"error": error or "Authentication required"}), 401

        _populate_g(payload)
        return await f(*args, **kwargs)

    return wrapper


def require_admin(f):

    @wraps(f)
    async def wrapper(*args, **kwargs):
        payload, error = await _authenticate()
        if error or payload is None:
            return jsonify({"error": error or "Authentication required"}), 401

        _populate_g(payload)
        current_user: User = await get_current_user(request)

        if current_user.role != AdminRole.ADMIN:
            return jsonify({"error": "Acesss Denied"}), 403

        return await f(*args, **kwargs)

    return wrapper
