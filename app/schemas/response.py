from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel
from enum import Enum

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    data: Optional[T] = None
    message: str = "Success"
    success: bool = True

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    BAD_REQUEST_ERROR = "BAD_REQUEST_ERROR"

class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[Any] = None

class ErrorResponseModel(BaseModel):
    success: bool = False
    message: str
    error: ErrorDetail
