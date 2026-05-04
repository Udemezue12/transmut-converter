from quart import Quart
from quart_schema import QuartSchema

from core.lifespan import LifespanService
from core.quart_cache_settings import QuartCache
from core.settings import settings
from middleware.csrf_middleware import register_csrf_middleware
from middleware.register_auth_middleware import register_middleware
from routes.auth_routes import AuthRoutes
from routes.conversion_routes import ConversionRoutes
from routes.converted_routes import ConvertedRoutes
from routes.csrf_token_routes import CsrfTokenRoutes
from routes.error_handlers import ErrorHandlers
from routes.html_template_routes import TemplatesRoutes
from routes.serve_media_routes import ServeMediaRoutes
from routes.upload_routes import UploadRoutes

app = Quart(__name__, static_folder='static',
            static_url_path='/static',
            template_folder='templates')

app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024 
app.config["MAX_FORM_MEMORY_SIZE"] = 500 * 1024 * 1024
app.config["BODY_TIMEOUT"] = 300
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.secret_key = settings.SECRET_KEY

QuartSchema(
    app,
    swagger_ui_path=None,
    redoc_ui_path=None,
    openapi_path=None,
    info={"title": "File Converter", "version": "1.0.0"},
)


LifespanService(app)
register_csrf_middleware(app)
register_middleware(app)
QuartCache(app)
ErrorHandlers(app)
CsrfTokenRoutes.register_route(app)
AuthRoutes.register_route(app)
ConversionRoutes.register_route(app)
ServeMediaRoutes.register_route(app)
UploadRoutes.register_route(app)
ConvertedRoutes.register_route(app)
TemplatesRoutes.register_route(app)


if __name__ == "__main__":
    app.run()
