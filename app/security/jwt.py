import os
import jwt
from jwt import PyJWTError
 
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set")
 
ALGORITHM = "HS256"
 
 
class InvalidTokenError(Exception):
    pass
 
 
class TokenPayload:
    def __init__(self, user_id: int, org_id: int, permissions: list[str]):
        self.user_id = user_id
        self.org_id = org_id
        self.permissions = permissions
 
 
def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
 
        user_id = payload.get("user_id")
        org_id = payload.get("org_id")
        permissions = payload.get("permissions", [])
        token_type = payload.get("type")
 
        if not user_id or not org_id:
            raise InvalidTokenError("Invalid token payload")
 
        if token_type != "access":
            raise InvalidTokenError("Invalid token type")
 
        return TokenPayload(
            user_id=user_id,
            org_id=org_id,
            permissions=permissions
        )
 
    except PyJWTError:
        raise InvalidTokenError("Invalid or expired token")