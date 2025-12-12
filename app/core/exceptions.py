"""
Custom exception classes for the application with standardized error responses.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

from app.core.schemas.response import ErrorCode


class AppException(HTTPException):
    """Base application exception with standardized error format."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize exception.
        
        Args:
            status_code: HTTP status code
            error_code: Application error code
            message: Error message
            field: Field name if validation error
            details: Additional error context
        """
        self.error_code = error_code
        self.field = field
        self.details = details
        
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message,
                    "field": field
                },
                "details": details
            }
        )


class AuthenticationError(AppException):
    """Authentication error (401)."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=message,
            details=details
        )


class PermissionDeniedError(AppException):
    """Permission denied error (403)."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            message=message,
            details=details
        )


class NotFoundError(AppException):
    """Resource not found error (404)."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            message=message,
            details=details
        )


class ConflictError(AppException):
    """Resource conflict error (409)."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            message=message,
            details=details
        )


class ValidationError(AppException):
    """Validation error (422)."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            message=message,
            field=field,
            details=details
        )


class RateLimitError(AppException):
    """Rate limit exceeded error (429)."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        retry_after: Optional[int] = None
    ):
        details = {"retry_after": retry_after} if retry_after else None
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=error_code,
            message=message,
            details=details
        )


def add_exception_handlers(app):
    """
    Add custom exception handlers to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        # Check if it's already our custom format
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        
        # Map status codes to error codes
        error_code_map = {
            401: ErrorCode.INVALID_TOKEN,
            403: ErrorCode.PERMISSION_DENIED,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
        }
        
        error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": str(exc.detail),
                    "field": None
                },
                "details": None
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:]) if len(error["loc"]) > 1 else None
            errors.append({
                "code": ErrorCode.FIELD_INVALID,
                "message": error["msg"],
                "field": field
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": "Request validation failed",
                    "field": None
                },
                "errors": errors
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        import traceback
        
        # Log the full traceback
        print(f"Unexpected error: {exc}")
        traceback.print_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR,
                    "message": "An unexpected error occurred",
                    "field": None
                },
                "details": {"error": str(exc)} if app.debug else None
            }
        )
