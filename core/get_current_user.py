from quart import Request

from auth_utils.auth_jwt import jwt_protect
from core.get_db import get_db_async
from repos.auth_repo import AuthRepo


async def get_current_user(request: Request):
    try:
        user_id = await jwt_protect(request)

        if not user_id:
            return None

        async with get_db_async() as db:
            return await AuthRepo(db).by_id(str(user_id))
    except Exception:
        return None
