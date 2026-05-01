import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_ctx = ContextVar("request_id", default="N/A")
user_id_ctx = ContextVar("user_id", default=None)
organization_id_ctx = ContextVar("organization_id", default=None)


class JsonFormatter(logging.Formatter):
    reserved = {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName",
    }

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": os.getenv("SERVICE_NAME", "payment-service"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "request_id": request_id_ctx.get(),
            "organization_id": organization_id_ctx.get(),
            "user_id": user_id_ctx.get(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in self.reserved and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    root_logger.handlers = []
    root_logger.addHandler(handler)
