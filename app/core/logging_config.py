import logging
import os
import sys
from contextvars import ContextVar

request_id_ctx = ContextVar("request_id", default="N/A")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get() or "N/A"
        return True


def setup_logging():
    service_name = os.getenv("SERVICE_NAME", "unknown-service")

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        f"%(asctime)s | %(levelname)s | %(request_id)s | {service_name} | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.handlers = []
    root_logger.addHandler(handler)