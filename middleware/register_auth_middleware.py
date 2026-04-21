
from time import time 
from quart import request, g, Response


def register_middleware(app):

    @app.before_request
    async def start_timer():
        g.start_time = time()          

    @app.after_request
    async def log_request(response: Response):
        start = getattr(g, "start_time", None)         
        if start is not None:
            duration = round((time() - start) * 1000, 2)
            print(f"[{request.method}] {request.path} → {response.status_code} ({duration}ms)")
            response.headers["X-Response-Time"] = f"{duration}ms"
        return response

    @app.after_request
    async def add_security_headers(response: Response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response