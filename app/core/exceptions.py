from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas.response import ErrorResponseModel, ErrorDetail, ErrorCode

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = ErrorCode.BAD_REQUEST_ERROR
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = ErrorCode.AUTHENTICATION_ERROR
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = ErrorCode.AUTHORIZATION_ERROR
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = ErrorCode.NOT_FOUND_ERROR
        elif exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            code = ErrorCode.INTERNAL_SERVER_ERROR

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponseModel(
                message=str(exc.detail),
                success=False,
                error=ErrorDetail(
                    code=code,
                    message=str(exc.detail)
                )
            ).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponseModel(
                message="Validation Error",
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Invalid input data",
                    details=exc.errors()
                )
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponseModel(
                message="Internal Server Error",
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_SERVER_ERROR,
                    message="An unexpected error occurred",
                    details=str(exc)
                )
            ).model_dump()
        )
