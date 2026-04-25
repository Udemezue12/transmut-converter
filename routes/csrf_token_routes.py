from quart import Blueprint
from quart_schema import tag

from core.throttling import rate_limiter_manager
from services.get_csrfToken_service import get_csrf_token

router = Blueprint("CSRF TOKEN", __name__, url_prefix="/api/v1")


class CsrfTokenRoutes:
    @classmethod
    def register_route(cls, app):
        app.register_blueprint(router)

    @staticmethod
    @router.get("/csrf_token")
    @tag(["CSRF TOKEN"])
    # @rate_limiter_manager.limit(times=5, seconds=10)
    def get_csrf_token():
        return get_csrf_token()