
from quart import request

from core.get_db import get_db_async
from repos.auth_repo import AuthRepo

from .auth_jwt import decode_access_token


class CookieJWTAuthentication:

    def extract_raw_token(self) -> str | None:

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1]

        return request.cookies.get("access_token")

    async def authenticate(self) -> dict | None:

        raw_token = self.extract_raw_token()
        if raw_token is None:
            return None
        async with get_db_async() as db:
            if await AuthRepo(db).is_token_blacklisted(raw_token):
                raise ValueError("Token is blacklisted")

        try:
            payload = decode_access_token(raw_token)
        except Exception as exc:
            raise ValueError(f"Invalid token: {exc}") from exc

        return payload
