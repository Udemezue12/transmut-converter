from quart import Response


class QuartCache:

    def __init__(self, app):
        self.app = app
        self._register_hooks()

    def _register_hooks(self):
        self.app.after_request(self.no_cache)

    @staticmethod
    async def no_cache(response:Response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
