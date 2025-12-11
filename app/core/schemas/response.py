"""
Standardized response schemas for API responses.
"""
from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

from app.constants.error_codes import ErrorCode

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str = Field(..., description="Error code (e.g., AUTH_001)")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if validation error")


class ErrorResponse(BaseModel):
    """Standardized error response."""
    success: bool = Field(False, description="Always false for errors")
    error: ErrorDetail
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "AUTH_001",
                    "message": "Invalid credentials",
                    "field": None
                },
                "details": None
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response with multiple field errors."""
    success: bool = Field(False, description="Always false for errors")
    error: ErrorDetail = Field(
        default=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed"
        )
    )
    errors: List[ErrorDetail] = Field(..., description="List of validation errors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed"
                },
                "errors": [
                    {
                        "code": "FIELD_REQUIRED",
                        "message": "Email is required",
                        "field": "email"
                    },
                    {
                        "code": "FIELD_INVALID",
                        "message": "Password must be at least 8 characters",
                        "field": "password"
                    }
                ]
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response."""
    success: bool = Field(True, description="Always true for success")
    message: str = Field(..., description="Success message")
    data: Optional[T] = Field(None, description="Response data")
    


class PaginatedData(BaseModel, Generic[T]):
    """Paginated data structure."""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")


class PaginatedResponse(SuccessResponse[PaginatedData[T]]):
    """Paginated response wrapper."""
    pass


# Helper functions to create error responses
def create_error_response(
    code: str,
    message: str,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        code: Error code
        message: Error message
        field: Field name if validation error
        details: Additional error context
        
    Returns:
        ErrorResponse instance
    """
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, field=field),
        details=details
    )


def create_validation_error_response(
    errors: List[Dict[str, str]]
) -> ValidationErrorResponse:
    """
    Create a validation error response.
    
    Args:
        errors: List of error dictionaries with 'code', 'message', 'field'
        
    Returns:
        ValidationErrorResponse instance
    """
    error_details = [
        ErrorDetail(
            code=err.get("code", ErrorCode.FIELD_INVALID),
            message=err["message"],
            field=err.get("field")
        )
        for err in errors
    ]
    
    return ValidationErrorResponse(errors=error_details)


def create_success_response(
    message: str,
    data: Optional[Any] = None
) -> SuccessResponse:
    """
    Create a success response.
    
    Args:
        message: Success message
        data: Response data
        
    Returns:
        SuccessResponse instance
    """
    return SuccessResponse(message=message, data=data)


# Backward compatibility alias
ResponseModel = SuccessResponse
