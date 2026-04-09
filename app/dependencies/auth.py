from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.security.jwt import decode_token
from app.exceptions.custom_exceptions import UnauthorizedException, ForbiddenException

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not credentials:
        raise UnauthorizedException("Authorization header missing")

    token = credentials.credentials

    try:
        payload = decode_token(token)
        return payload
    except Exception:
        raise UnauthorizedException("Invalid or expired token")