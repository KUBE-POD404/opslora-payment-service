from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.custom_exceptions import AppException


# -----------------------------
# Custom Application Exceptions
# -----------------------------
def app_exception_handler(exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message
        }
    )


# -----------------------------
# FastAPI HTTP Exceptions
# -----------------------------
def http_exception_handler(exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail
        }
    )


# -----------------------------
# Validation Errors
# -----------------------------
def validation_exception_handler(exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors()
        }
    )


# -----------------------------
# Unhandled Errors
# -----------------------------
def generic_exception_handler():
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error"
        }
    )