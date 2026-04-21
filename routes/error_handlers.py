import logging

from quart import jsonify, render_template, request
from quart_schema import RequestSchemaValidationError

logger = logging.getLogger(__name__)


class ErrorHandlers:
    def __init__(self, app):
        self.app = app
        self._register()

    @staticmethod
    async def _respond(html_template: str, code: int, message: str):
        if (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        ):
            return jsonify({"error": message, "status": code}), code
        return await render_template(html_template), code

    def _register(self):
        @self.app.errorhandler(RequestSchemaValidationError)
        async def handle_validation_error(error: RequestSchemaValidationError):
            return jsonify(
                {
                    "error": "Validation failed",
                    "details": error.validation_error.errors() if hasattr(error.validation_error, 'errors') else str(error.validation_error),
                }
            ), 400

        @self.app.errorhandler(400)
        async def bad_request(error):
            logger.warning("400 Bad Request: %s | path=%s",
                           error, request.path)
            return await self._respond(
                "error_pages/400.html", 400, "Bad request"
            )

        @self.app.errorhandler(401)
        async def unauthorized(error):
            logger.warning("401 Unauthorized: %s | path=%s",
                           error, request.path)
            return await self._respond(
                "error_pages/401.html", 401, "Authentication required"
            )

        @self.app.errorhandler(403)
        async def forbidden(error):
            logger.warning(
                "403 Forbidden: %s | path=%s | ip=%s",
                error, request.path, request.remote_addr,
            )
            return await self._respond(
                "error_pages/403.html", 403, "Access denied"
            )

        @self.app.errorhandler(404)
        async def page_not_found(error):
            logger.info("404 Not Found: path=%s", request.path)
            return await self._respond(
                "error_pages/404.html", 404, "Resource not found"
            )

        @self.app.errorhandler(405)
        async def method_not_allowed_error(error):
            logger.warning(
                "405 Method Not Allowed: %s %s", request.method, request.path
            )
            return jsonify({
                "error": f"Method {request.method} not allowed on {request.path}",
                "status": 405,
            }), 405

        @self.app.errorhandler(406)
        async def not_acceptable_error(error):

            logger.warning(
                "406, Not Acceptable: %s %s", request.method, request.path
            )
            return await self._respond(
                "error_pages/406.html", 406, "Not Acceptable"
            )

        @self.app.errorhandler(408)
        async def request_timeout_error(error):
            return jsonify({
                "error": "Request timed out",
                "status": 408,
            }), 408

        @self.app.errorhandler(409)
        async def conflict_error(error):
            logger.warning("409 Conflict: %s | path=%s", error, request.path)
            return jsonify({
                "error": "Resource conflict",
                "status": 409,
            }), 409

        @self.app.errorhandler(410)
        def gone_error(error):
            logger.info("410 Gone: path=%s", request.path)
            return jsonify({
                "error": "Resource no longer available",
                "status": 410,
            }), 410

        @self.app.errorhandler(411)
        def length_required_error(error):

            logger.info("411, Length Require: path=%s", request.path)
            return jsonify({
                "error": "Length Required",
                "status": 411,
            }), 411

        @self.app.errorhandler(412)
        def precondition_failed_error(error):
            logger.info("412, Precondition Error: path=%s", request.path)
            return jsonify({
                "error": "Precondition Error",
                "status": 412,
            }), 412

        @self.app.errorhandler(413)
        async def payload_too_large(error):
            logger.warning(
                "413 Payload Too Large: path=%s | ip=%s",
                request.path, request.remote_addr,
            )
            return jsonify({
                "error": "File exceeds the maximum allowed size",
                "status": 413,
            }), 413

        @self.app.errorhandler(414)
        async def uri_too_long_error(error):
            logger.info("414, URI Too Long: path=%s", request.path)
            return jsonify({
                "error": "Uri Too Long",
                "status": 414,
            }), 414

        @self.app.errorhandler(415)
        async def unsupported_media_type_error(error):
            logger.warning(
                "415 Unsupported Media Type: path=%s | content-type=%s",
                request.path, request.content_type,
            )
            return jsonify({
                "error": "Unsupported file or media type",
                "status": 415,
            }), 415

        @self.app.errorhandler(416)
        async def range_not_satisfiable_error(error):
            logger.warning(
                "416 Unsupported Media Type: path=%s | content-type=%s",
                request.path, request.content_type,
            )
            return jsonify({
                "error": "Unsupported file or media type",
                "status": 416,
            }), 416

        @self.app.errorhandler(417)
        async def expectation_failed_error(error):
            logger.warning(
                "417 Expectation Failed: path=%s | content-type=%s",
                request.path, request.content_type,
            )
            return jsonify({
                "error": "Expectation Failed",
                "status": 417,
            }), 417

        @self.app.errorhandler(418)
        async def im_a_teapot_error(error):
            logger.warning(
                "417 Teapot Error : path=%s | content-type=%s",
                request.path, request.content_type,
            )
            return jsonify({
                "error": "Teapot Error",
                "status": 418,
            }), 418

        @self.app.errorhandler(422)
        async def unprocessable_entity_error(error):
            logger.warning("422 Validation Error: %s | path=%s",
                           error, request.path)
            return jsonify({
                "error": "Validation failed",
                "detail": str(error) if error else None,
                "status": 422,
            }), 422

        @self.app.errorhandler(423)
        async def locked_error(error):
            logger.warning("423 Locked Error: %s | path=%s",
                           error, request.path)
            return jsonify({
                "error": "Error, Locked",
                "detail": str(error) if error else None,
                "status": 423,
            }), 423

        @self.app.errorhandler(424)
        async def failed_dependency_error(error):
            logger.warning("424 Failed Dependency: %s | path=%s",
                           error, request.path)
            return jsonify({
                "error": "Failed Dependency",
                "detail": str(error) if error else None,
                "status": 424,
            }), 424

        @self.app.errorhandler(428)
        async def precondition_required_error(error):
            return await self._respond("error_pages/428.html", 428, "Precondition Required")

        @self.app.errorhandler(429)
        async def too_many_requests_error(error):
            logger.warning(
                "429 Rate Limited: path=%s | ip=%s",
                request.path, request.remote_addr,
            )
            return await self._respond(
                "error_pages/429.html", 429, "Too many requests — slow down"
            )

        @self.app.errorhandler(431)
        async def request_header_fields_too_large_error(error):
            logger.warning(
                "431 Request Header Fields Too Large: path=%s | ip=%s",
                request.path, request.remote_addr,
            )
            return await self._respond(
                "error_pages/431.html", 431, "Request Header Fields Too Large — slow down"
            )

        @self.app.errorhandler(451)
        async def unavailable_for_legal_reasons_error(error):

            logger.warning(
                "431 Unavailable for Legal Reasons Error: path=%s | ip=%s",
                request.path, request.remote_addr,
            )
            return await self._respond(
                "error_pages/451.html", 451, "Unavailable for Legal Reasons Error"
            )

        @self.app.errorhandler(500)
        async def internal_server_error(error):
            logger.exception(
                "500 Internal Server Error: %s | path=%s", error, request.path
            )
            return await self._respond(
                "error_pages/500.html", 500, "An unexpected error occurred"
            )

        @self.app.errorhandler(501)
        async def not_implemented_error(error):
            logger.warning(
                "501 Not Implemented Error: %s | path=%s", error, request.path)
            return jsonify({
                "error": "Not Implemented Error",
                "detail": str(error) if error else None,
                "status": 501,
            }), 501

        @self.app.errorhandler(502)
        async def bad_gateway_error(error):
            logger.error("502 Bad Gateway: %s | path=%s", error, request.path)
            return jsonify({
                "error": "Bad gateway — upstream service error",
                "status": 502,
            }), 502

        @self.app.errorhandler(503)
        async def service_unavailable(error):
            logger.error(
                "503 Service Unavailable: %s | path=%s", error, request.path
            )
            return await self._respond(
                "error_pages/503.html", 503, "Service temporarily unavailable"
            )

        @self.app.errorhandler(504)
        async def gateway_timeout(error):
            logger.error("504 Gateway Timeout: path=%s", request.path)
            return jsonify({
                "error": "Gateway timed out",
                "status": 504,
            }), 504

        @self.app.errorhandler(505)
        async def http_version_not_supported_error(error):
            logger.error(
                "505 HTTP Version Not Supported: %s | path=%s", error, request.path
            )
            return await self._respond(
                "error_pages/505.html", 505, "HTTP Version Not Supported"
            )
