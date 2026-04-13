from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
 
from app.security.jwt import decode_token, InvalidTokenError
from app.exceptions.custom_exceptions import UnauthorizedException
 
security = HTTPBearer(auto_error=False)
 
 
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authorization header missing")
 
    if credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Invalid authentication scheme")
 
    token = credentials.credentials
 
    try:
        return decode_token(token)
    except InvalidTokenError:
        raise UnauthorizedException("Invalid or expired token")