"""
Permission constants for RBAC system.
"""
from enum import Enum


class PermissionEnum(str, Enum):
    """Predefined permission scopes."""
    # User permissions
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    
    # Role permissions
    ROLES_READ = "roles:read"
    ROLES_WRITE = "roles:write"
    ROLES_DELETE = "roles:delete"
    
    # Permission permissions
    PERMISSIONS_READ = "permissions:read"
    PERMISSIONS_WRITE = "permissions:write"
    PERMISSIONS_DELETE = "permissions:delete"
    
    # OAuth Provider permissions
    OAUTH_PROVIDERS_READ = "oauth_providers:read"
    OAUTH_PROVIDERS_WRITE = "oauth_providers:write"
    OAUTH_PROVIDERS_DELETE = "oauth_providers:delete"
    
    # Admin management
    ADMINS_MANAGE = "admins:manage"
    
    # Order permissions
    ORDERS_READ = "orders:read"
    ORDERS_WRITE = "orders:write"
    
    # Product permissions
    PRODUCTS_READ = "products:read"
    PRODUCTS_WRITE = "products:write"
    
    # System permissions
    SYSTEM_CONFIG = "system:config"


# Default role-to-permission mappings
DEFAULT_ROLE_PERMISSIONS = {
    "SUPER_ADMIN": ["*"],  # All permissions
    "MANAGER": [
        PermissionEnum.USERS_READ,
        PermissionEnum.USERS_WRITE,
        PermissionEnum.ORDERS_READ,
        PermissionEnum.ORDERS_WRITE,
        PermissionEnum.PRODUCTS_READ,
        PermissionEnum.PRODUCTS_WRITE,
    ],
    "SUPPORT": [
        PermissionEnum.USERS_READ,
        PermissionEnum.ORDERS_READ,
    ],
    "CUSTOMER": [
        "profile:read",
        "profile:write",
        PermissionEnum.ORDERS_READ,
    ],
}
