"""
API v1 router.
"""
from fastapi import APIRouter

from app.modules.auth import endpoints as auth
from app.modules.roles import endpoints as roles
from app.modules.roles import permissions_endpoints as permissions
from app.modules.oauth import endpoints as oauth
from app.modules.oauth import provider_endpoints as oauth_providers
from app.modules.users import admin_endpoints as admins
from app.modules.users import customer_endpoints as customers
from app.modules.audit import endpoints as audit_logs


api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(oauth.router, prefix="/auth/oauth")
api_router.include_router(roles.router, prefix="/admin/roles")
api_router.include_router(permissions.router, prefix="/admin/permissions")
api_router.include_router(oauth_providers.router, prefix="/admin/oauth-providers")
api_router.include_router(admins.router, prefix="/admin/admins")
api_router.include_router(customers.router, prefix="/admin/customers")
api_router.include_router(audit_logs.router, prefix="/admin/audit-logs")

