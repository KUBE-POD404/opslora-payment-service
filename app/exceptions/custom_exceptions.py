class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
        code: str = "APP_ERROR",
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        self.code = code
        super().__init__(message, status_code, details, code)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: dict | None = None):
        super().__init__(message, 404, details, "NOT_FOUND")


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", details: dict | None = None):
        super().__init__(message, 401, details, "UNAUTHORIZED")


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", details: dict | None = None):
        super().__init__(message, 403, details, "FORBIDDEN")


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", details: dict | None = None):
        super().__init__(message, 409, details, "CONFLICT")
