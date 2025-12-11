from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import add_exception_handlers
from app.core.docs import create_error_responses
from app.core.lifespan import lifespan

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    responses=create_error_responses(400, 401, 403, 404, 422, 429, 500),
    lifespan=lifespan  # Auto-initialize database on startup
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

# Add rate limiting middleware (60 requests per minute globally)
from app.core.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, limit=60, window=60)

add_exception_handlers(app)

from app.core.schemas.response import SuccessResponse
from app.core.docs import doc_responses

@app.get(
    "/health",
    response_model=SuccessResponse,
    summary="Health Check",
    responses=doc_responses(
        success_example={"status": "ok", "version": "1.0.0"},
        success_message="System is healthy",
        errors=()  # No auth required for health check
    )
)
async def health_check():
    """Check if the API is running and healthy."""
    return SuccessResponse(
        data={"status": "ok", "version": "1.0.0"},
        message="System is healthy"
    )

# Include API routes
from app.api.v1.router import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

