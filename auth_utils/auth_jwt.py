import datetime

from jose import jwt
from quart import Request

from core.settings import settings
from schemas.schema import TokenPair

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

ACCESS_EXP_MINUTES = 15
REFRESH_EXP_DAYS = 7


def create_access_token(user_id: str) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(minutes=ACCESS_EXP_MINUTES),
            "type": "access",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: str) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(days=REFRESH_EXP_DAYS),
            "type": "refresh",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_token_pair(user_id: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(str(user_id)),
        refresh_token=create_refresh_token(str(user_id)),
    )


def decode_access_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def decode_refresh_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def jwt_protect(request: Request):
    try:
        token = request.cookies.get("access_token")

        if not token:
            return None

        payload = decode_access_token(str(token))

        if not payload:
            return None

        user_id = payload.get("sub")   

        if not user_id:
            return None

        return user_id  

    except Exception:
        return None