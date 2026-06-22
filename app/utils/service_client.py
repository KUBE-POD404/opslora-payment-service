import logging
import time
import uuid

import requests

from app.core.logging_config import request_id_ctx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 5


def authenticated_get(url: str, token: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    request_id = request_id_ctx.get() or str(uuid.uuid4())
    started = time.perf_counter()

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": token,
                "X-Request-ID": request_id,
            },
            timeout=timeout,
        )
        logger.info(
            "service_call_completed",
            extra={
                "event": "service_call_completed",
                "method": "GET",
                "target_url": url,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response
    except requests.RequestException:
        logger.exception(
            "service_call_failed",
            extra={"event": "service_call_failed", "method": "GET", "target_url": url},
        )
        raise


def authenticated_post(
    url: str,
    token: str,
    json: dict,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
):
    request_id = request_id_ctx.get() or str(uuid.uuid4())
    started = time.perf_counter()

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": token,
                "X-Request-ID": request_id,
            },
            json=json,
            timeout=timeout,
        )
        logger.info(
            "service_call_completed",
            extra={
                "event": "service_call_completed",
                "method": "POST",
                "target_url": url,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response
    except requests.RequestException:
        logger.exception(
            "service_call_failed",
            extra={"event": "service_call_failed", "method": "POST", "target_url": url},
        )
        raise
