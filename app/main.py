from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import (
    APIError,
    api_error_handler,
    error_response,
    unhandled_error_handler,
)
from app.routers import auth, health, trips

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Trip Planner API",
    version="1.0.0",
    description="Backend API for the AI Trip Planner mobile app. "
    "The mobile frontend never touches the database directly — it calls this API only.",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, lambda request, exc: error_response(
    "Invalid request. Please check the submitted data.", 422
))
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(trips.router)
