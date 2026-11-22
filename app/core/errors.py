from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("trip-planner")


class APIError(Exception):
    """An error safe to show to the client."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return error_response(exc.message, exc.status_code)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the real error server-side; never leak stack traces to clients.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error_response("Something went wrong. Please try again.", 500)
