"""
API v1 router.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, roles, permissions, oauth, oauth_providers

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(oauth.router, prefix="/auth/oauth")
api_router.include_router(roles.router, prefix="/admin/roles")
api_router.include_router(permissions.router, prefix="/admin/permissions")
api_router.include_router(oauth_providers.router, prefix="/admin/oauth-providers")

