from typing import Any, Dict, List, Union, Type
from pydantic import BaseModel
from app.schemas.response import ErrorResponseModel, ErrorCode

def create_error_responses(*status_codes: int) -> Dict[int, Dict[str, Any]]:
    """
    Create a dictionary of error responses for OpenAPI documentation with specific examples.
    """
    responses = {}
    
    # Mapping of status codes to specific error codes and messages
    error_map = {
        400: (ErrorCode.BAD_REQUEST_ERROR, "Bad Request"),
        401: (ErrorCode.AUTHENTICATION_ERROR, "Not Authenticated"),
        403: (ErrorCode.AUTHORIZATION_ERROR, "Not Authorized"),
        404: (ErrorCode.NOT_FOUND_ERROR, "Resource Not Found"),
        422: (ErrorCode.VALIDATION_ERROR, "Validation Error"),
        500: (ErrorCode.INTERNAL_SERVER_ERROR, "Internal Server Error"),
    }

    for status in status_codes:
        code, msg = error_map.get(status, (ErrorCode.BAD_REQUEST_ERROR, "Error"))
        
        responses[status] = {
            "model": ErrorResponseModel,
            "description": msg,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": msg,
                        "error": {
                            "code": code,
                            "message": msg,
                            "details": None
                        }
                    }
                }
            }
        }
    return responses
