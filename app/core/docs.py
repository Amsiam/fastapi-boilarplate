"""
OpenAPI documentation utilities and decorators.
"""
from typing import Dict, Any, Optional, Callable
from functools import wraps
from fastapi import status
from app.core.schemas.response import ErrorResponse, SuccessResponse, ErrorCode


def create_error_responses(*status_codes: int) -> Dict[int | str, Dict[str, Any]]:
    """
    Create error response models for OpenAPI documentation with specific examples.
    
    Args:
        status_codes: HTTP status codes to include
        
    Returns:
        Dictionary of status codes to response models with examples
    """
    # Detailed error examples for each status code
    error_examples = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.VALIDATION_ERROR,
                            "message": "Invalid request parameters",
                            "field": None
                        },
                        "details": None
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Unauthorized - Invalid or missing authentication",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.INVALID_CREDENTIALS,
                            "message": "Invalid email or password",
                            "field": None
                        },
                        "details": None
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Forbidden - Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.PERMISSION_DENIED,
                            "message": "You don't have permission to access this resource",
                            "field": None
                        },
                        "details": None
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Not Found - Resource does not exist",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.USER_NOT_FOUND,
                            "message": "User not found",
                            "field": None
                        },
                        "details": None
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Conflict - Resource already exists",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.USER_ALREADY_EXISTS,
                            "message": "User with this email already exists",
                            "field": "email"
                        },
                        "details": None
                    }
                }
            }
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Validation Error - Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.VALIDATION_ERROR,
                            "message": "Request validation failed",
                            "field": None
                        },
                        "errors": [
                            {
                                "code": ErrorCode.FIELD_REQUIRED,
                                "message": "Email is required",
                                "field": "email"
                            }
                        ]
                    }
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                            "message": "Too many requests. Please try again later.",
                            "field": None
                        },
                        "details": {"retry_after": 60}
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": ErrorCode.INTERNAL_ERROR,
                            "message": "An unexpected error occurred",
                            "field": None
                        },
                        "details": None
                    }
                }
            }
        },
    }
    
    responses = {}
    for code in status_codes:
        if code in error_examples:
            responses[code] = error_examples[code]
    
    return responses


from pydantic import BaseModel

def doc_responses(
    success_example: Optional[Any] = None,
    success_message: str = "Operation completed successfully",
    success_status_code: int = status.HTTP_200_OK,
    errors: tuple = ()
) -> Dict[int | str, Dict[str, Any]]:
    """
    Create complete response documentation (success + errors) for an endpoint.
    
    Usage:
        @app.get("/users", responses=doc_responses(
            success_example={"id": "123", "name": "John"},
            errors=(401, 403, 404)
        ))
        
        # Or with a Pydantic model (uses Config.json_schema_extra['example'])
        @app.get("/users", responses=doc_responses(
            success_example=UserResponse,
            success_status_code=200
        ))
    
    Args:
        success_example: Example data dict OR Pydantic model class
        success_message: Success message
        success_status_code: Success HTTP status code (default: 200)
        errors: Tuple of error status codes to document
        
    Returns:
        Complete responses dict for FastAPI
    """
    responses = create_error_responses(*errors)
    

    # 2. Add specific success example if provided as a dictionary
    #    If success_example is a dict, we use it to override the default example.
    #    If it is a class or None, we let FastAPI's response_model handle the 
    #    schema and example generation automatically.
    if isinstance(success_example, dict):
        responses[success_status_code] = {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": success_message,
                        "data": success_example
                    }
                }
            }
        }
    
    return responses

