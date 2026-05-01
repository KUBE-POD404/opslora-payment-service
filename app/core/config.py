import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


@dataclass(frozen=True)
class Settings:
    service_name: str = os.getenv("SERVICE_NAME", "payment-service")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    database_url: str = _required("DATABASE_URL")
    jwt_secret_key: str = _required("JWT_SECRET_KEY")
    invoice_service_url: str = _required("INVOICE_SERVICE_URL")
    api_version: str = os.getenv("API_VERSION", "/api/v1")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
