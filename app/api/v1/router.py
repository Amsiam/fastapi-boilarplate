"""
API v1 router.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, roles, permissions

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
