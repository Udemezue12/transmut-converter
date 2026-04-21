
import secrets

from quart import Request, jsonify, request, session

CSRF_EXEMPT_PATHS = {"/docs", "/openapi.json", "/redoc", "/static"}


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def is_csrf_exempt(path: str) -> bool:
    return any(path.startswith(exempt) for exempt in CSRF_EXEMPT_PATHS)


async def validate_csrf(request:Request):
    
    session_token = session.get("csrf_token")
    cookie_token  = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token") 

    if not (session_token and cookie_token):
        return jsonify({"error": "Missing CSRF token"}), 403

    # if header_token != cookie_token:                    
    #     return jsonify({"error": "CSRF token mismatch (header vs cookie)"}), 403

    if session_token != cookie_token:
        return jsonify({"error": "Invalid CSRF token: mismatch with session token"}), 403

    return None  


def register_csrf_middleware(app):

    @app.before_request
    async def csrf_protect():
        
        if is_csrf_exempt(request.path):
            return

        
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return

        error = await validate_csrf(request)
        if error is not None:
            return error    

    

        
        