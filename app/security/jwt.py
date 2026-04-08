import os
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"


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
            algorithms=[ALGORITHM]
        )

        return TokenPayload(
            user_id=payload.get("user_id"),
            org_id=payload.get("org_id"),
            permissions=payload.get("permissions", [])
        )

    except JWTError:
        raise Exception("Invalid or expired token")