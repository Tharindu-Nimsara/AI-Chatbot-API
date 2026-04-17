import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response automatically.
    Runs on every request — no need to add to individual routes.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Add security headers to the response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"

        # Log every request with timing
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} | "
            f"status: {response.status_code} | "
            f"time: {process_time:.1f}ms"
        )

        return response