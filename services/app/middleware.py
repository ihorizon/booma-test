import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = logging.getLogger("booma.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        log.info("%s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            log.exception("%s %s failed before response", request.method, request.url.path)
            raise
        ms = (time.perf_counter() - start) * 1000
        log.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, ms)
        return response
