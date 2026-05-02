from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine

router = APIRouter(prefix="/payments", tags=["health"])


@router.get("/health")
@router.get("/live")
def live():
    return {"status": "ok"}


@router.get("/startup")
def startup():
    return live()


@router.get("/ready")
def ready():
    checks = {"database": "ok"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "error"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}
