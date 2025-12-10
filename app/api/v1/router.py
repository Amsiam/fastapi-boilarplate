"""
API v1 router.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, roles, permissions, oauth

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(oauth.router, prefix="/auth/oauth", tags=["oauth"])
api_router.include_router(roles.router, prefix="/admin/roles", tags=["roles"])
api_router.include_router(permissions.router, prefix="/admin/permissions", tags=["permissions"])
