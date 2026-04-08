import os
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.middleware import RequestContextMiddleware

from app.routers.v1 import payments

from app.exceptions.custom_exceptions import AppException
from app.exceptions.handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

from app.core.logging_config import setup_logging
setup_logging()

if os.getenv("ENVIRONMENT") == "production":
    docs_url = None
    redoc_url = None
    openapi_url = None
else:
    docs_url = "/payments/docs"
    redoc_url = "/payments/redoc"
    openapi_url = "/payments/openapi.json"

app = FastAPI(
    title="Payment Service",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)



# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(payments.router,prefix="/api/v1")