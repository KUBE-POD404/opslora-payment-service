import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import request_id_ctx

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        request_id_ctx.set(request_id)

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response