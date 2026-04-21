from functools import wraps

from quart import g, jsonify

from .auth_cookie_middleware import CookieJWTAuthentication


def require_auth(f):
   
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            payload = await CookieJWTAuthentication().authenticate()
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

        if payload is None:
            return jsonify({"error": "Authentication required"}), 401

        g.current_user    = payload
        g.current_user_id = payload["sub"]
       
        return await f(*args, **kwargs)
    return wrapper


def require_role(*roles: str):
    
    def decorator(f):
        @wraps(f)
        @require_auth
        async def wrapper(*args, **kwargs):
            if g.current_role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return await f(*args, **kwargs)
        return wrapper
    return decorator