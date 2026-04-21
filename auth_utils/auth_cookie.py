from quart import Response

from core.settings import settings
from models.enums import ENVSettings

ACCESS_COOKIE_MAX_AGE = 15 * 60
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60
ENV = settings.ENV
path: str = "/"
samesite: str = "Lax"


def set_auth_cookies(
    response: Response, access_token: str, refresh_token: str
) -> Response:
    if ENV == ENVSettings.Production:
        response.set_cookie(
            "access_token",
            access_token,
            max_age=ACCESS_COOKIE_MAX_AGE,
            httponly=True,
            secure=True,
            samesite=samesite,
            path=path
        )
        response.set_cookie(
            "refresh_token",
            refresh_token,
            max_age=REFRESH_COOKIE_MAX_AGE,
            httponly=True,
            secure=True,
            samesite=samesite,
            path=path,
        )
        return response
    else:
        response.set_cookie(
            "access_token",
            access_token,
            max_age=ACCESS_COOKIE_MAX_AGE,
            httponly=True,
            secure=False,
            samesite=samesite,
            path=path,
        )
        response.set_cookie(
            "refresh_token",
            refresh_token,
            max_age=REFRESH_COOKIE_MAX_AGE,
            httponly=True,
            secure=False,
            samesite=samesite,
            path=path,
        )
        return response


def set_auth_access_token(response: Response, access_token: str) -> Response:
    if ENV == ENVSettings.Production:
        response.set_cookie(
            "access_token",
            access_token,
            max_age=ACCESS_COOKIE_MAX_AGE,
            httponly=True,
            secure=True,
            samesite=samesite,
            path=path,
        )
        return response
    else:
        response.set_cookie(
            "access_token",
            access_token,
            max_age=ACCESS_COOKIE_MAX_AGE,
            httponly=True,
            secure=False,
            samesite=samesite,
            path=path,
        )
        return response


def clear_auth_cookies(response: Response) -> Response:
    cookies = ["access_token", "refresh_token",
               "csrf_token", "session", "csrftoken"]

    if not cookies:
        return response
    is_production = settings.ENV == ENVSettings.Production

    unique_cookies = set(cookies)

    for key in unique_cookies:
        response.delete_cookie(
            key=key, path=path, samesite=samesite, secure=is_production)

    return response
