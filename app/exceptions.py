from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import logging

logger = logging.getLogger("rickmorty-api")

def setup_exception_handlers(app):
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        logger.warning("Rate limit exceeded: %s", request.client)
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Please try again later."},
        )

    @app.exception_handler(400)
    async def bad_request_handler(request: Request, exc):
        return JSONResponse(
            status_code=400,
            content={"error": "Bad request"},
        )

    @app.exception_handler(503)
    async def service_unavailable_handler(request: Request, exc):
        return JSONResponse(
            status_code=503,
            content={"error": "Service temporarily unavailable"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
