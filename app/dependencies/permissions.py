from fastapi import Depends
from app.dependencies.auth import get_current_user
from app.exceptions.custom_exceptions import ForbiddenException
from app.security.jwt import TokenPayload
 
 
def require_permission(permission: str):
 
    def permission_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ):
        if permission not in current_user.permissions:
            raise ForbiddenException("Insufficient permissions")
 
        return current_user
 
    return permission_checker