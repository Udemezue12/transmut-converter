
from quart_cors import cors

from .settings import settings


class QuartCors:
    def __init__(self, app) -> None:
        cors(
            app,
            allow_origin=settings.ALLOWED_HOSTS,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
            allow_credentials=True,
            max_age=600,
        )
