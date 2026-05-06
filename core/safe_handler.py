import logging
from functools import wraps
from typing import Any, Callable, cast

from quart import Request, jsonify
from quart import request as quart_request
from werkzeug.exceptions import HTTPException

from .friendly_msgs import get_friendly_message

logger = logging.getLogger(__name__)


def _extract_request(*args: Any, **kwargs: Any) -> Request | None:
    for arg in list(args) + list(kwargs.values()):
        if isinstance(arg, Request):
            return arg
    try:
        return cast(Request, getattr(quart_request, "__wrapped__", quart_request))
    except RuntimeError:
        return None


def _build_log_context(req: Request, func_name: str) -> dict[str, str]:
    client_ip = req.remote_addr or "unknown"
    return {
        "func": func_name,
        "path": req.full_path,
        "client_ip": client_ip,
        "trace_id": req.headers.get("X-Request-ID", "none"),
        "method": req.method,
    }


def safe_handler(func: Callable) -> Callable:

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        req = _extract_request(*args, **kwargs)
        ctx = _build_log_context(req, func.__name__) if req else {"func": func.__name__}

        try:
            return await func(*args, **kwargs)

        except HTTPException as exc:
            if req:
                logger.warning(
                    "[HTTPException] TraceID=%(trace_id)s | %(method)s %(path)s "
                    "from %(client_ip)s → %(status)s",
                    {**ctx, "status": f"{exc.code} {exc.name}", "detail": exc.description},
                )
            else:
                logger.warning(
                    "[HTTPException] func=%(func)s | %(status)s",
                    {**ctx, "status": f"{exc.code}"},
                )
            friendly = get_friendly_message(exc)

           
            return jsonify({"detail": friendly}), exc.code

        except Exception as exc:  
            if req:
                logger.error(
                    "[UnhandledError] TraceID=%(trace_id)s | func=%(func)s | "
                    "%(method)s %(path)s from %(client_ip)s | error=%(error)r",
                    {**ctx, "error": exc},
                    exc_info=True,
                )
            else:
                logger.error(
                    "[UnhandledError] func=%(func)s | error=%(error)r",
                    {**ctx, "error": exc},
                    exc_info=True,
                )

            friendly = get_friendly_message(exc)
          
            return jsonify({"detail": friendly}), 500

    return wrapper