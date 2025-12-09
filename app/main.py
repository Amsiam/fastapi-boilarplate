from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import add_exception_handlers
from app.core.docs import create_error_responses

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    responses=create_error_responses(400, 401, 403, 404, 422, 500)
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

add_exception_handlers(app)

from app.schemas.response import ResponseModel

@app.get("/health", response_model=ResponseModel[dict])
async def health_check():
    return ResponseModel(data={"status": "ok"}, message="System is healthy")
