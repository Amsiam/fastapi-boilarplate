"""
Permission management and RBAC utilities.
"""
from typing import List, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.modules.users.models import User
from app.constants import PermissionEnum, DEFAULT_ROLE_PERMISSIONS


# OAuth2 scheme for Swagger UI (supports both password flow and bearer token)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False  # Don't auto-error, we'll handle it manually
)

# Alternative: HTTP Bearer scheme (simpler for Swagger)
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.
    Supports multiple token sources for flexibility:
    1. OAuth2 password flow (Swagger UI "Authorize" button)
    2. HTTP Bearer token (Authorization header)
    3. Manual Authorization header
    
    Args:
        token: Token from OAuth2 scheme
        credentials: Token from HTTP Bearer scheme
        authorization: Raw Authorization header
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    from app.modules.users.repository import UserRepository
    from app.core.cache import get_cache
    from app.core.exceptions import AuthenticationError, NotFoundError
    from app.core.schemas.response import ErrorCode
    
    # Try to extract token from multiple sources
    access_token = None
    
    # Strict Header Support Only
    # OAuth2PasswordBearer checks 'Authorization: Bearer <token>'
    if token:
        access_token = token
    elif credentials:
        access_token = credentials.credentials
    # removed manual Authorization header check which allowed non-strict parsing or potential confusion
    # The Depends(oauth2_scheme) and Depends(http_bearer) are the standard ways ensuring header usage.
    
    if not access_token:
        raise AuthenticationError(
            error_code=ErrorCode.INVALID_TOKEN,
            message="Not authenticated"
        )
    
    # Check if token is blacklisted (logged out)
    # Use hash of token to avoid storing full token in Redis
    import hashlib
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()
    blacklist_key = f"blacklist:token:{token_hash}"
    is_blacklisted = await get_cache(blacklist_key)
    if is_blacklisted:
        raise AuthenticationError(
            error_code=ErrorCode.INVALID_TOKEN,
            message="Token has been revoked"
        )
    
    # Decode token
    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise AuthenticationError(
            error_code=ErrorCode.INVALID_TOKEN,
            message="Invalid authentication token"
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise AuthenticationError(
            error_code=ErrorCode.INVALID_TOKEN,
            message="Invalid token payload"
        )
    
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    
    if user is None:
        raise NotFoundError(
            error_code=ErrorCode.USER_NOT_FOUND,
            message="User not found"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object
        
    Raises:
        AuthenticationError: If user is inactive
    """
    from app.core.exceptions import AuthenticationError
    from app.core.schemas.response import ErrorCode
    
    if not current_user.is_active:
        raise AuthenticationError(
            error_code=ErrorCode.ACCOUNT_INACTIVE,
            message="Account is inactive"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current verified user (for customers).
    
    Args:
        current_user: Current active user
        
    Returns:
        User object
        
    Raises:
        AuthenticationError: If user email is not verified
    """
    from app.core.exceptions import AuthenticationError
    from app.core.schemas.response import ErrorCode
    
    if not current_user.is_verified:
        raise AuthenticationError(
            error_code=ErrorCode.EMAIL_NOT_VERIFIED,
            message="Email not verified. Please verify your email to continue."
        )
    return current_user


async def get_user_permissions(user: User, db: AsyncSession) -> List[str]:
    """
    Get all permissions for a user (role permissions + overrides).
    Uses Redis cache for performance (5 minute TTL).
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        List of permission codes
    """
    from app.constants.enums import UserType
    from app.modules.users.repository import AdminRepository
    from app.modules.roles.repository import RoleRepository
    from app.core.cache import get_cache, set_cache, user_permissions_key
    
    # Customers have fixed permissions (no caching needed)
    if user.user_type == UserType.CUSTOMER:
        return DEFAULT_ROLE_PERMISSIONS["CUSTOMER"]
    
    # Check cache first
    cache_key = user_permissions_key(str(user.id))
    cached_data = await get_cache(cache_key)
    
    # Verify version if cached
    if cached_data:
        # Backward compatibility or if stored as list
        if isinstance(cached_data, list):
            # No version check possible for old format, treat as valid or miss
            # Let's treat as miss to force update
            pass 
        elif isinstance(cached_data, dict):
            cached_role_id = cached_data.get("role_id")
            cached_version = cached_data.get("role_version", 0)
            cached_perms = cached_data.get("permissions", [])
            
            if cached_role_id:
                # Check current version in Redis
                current_version = await get_cache(f"role:version:{cached_role_id}")
                current_version = int(current_version) if current_version else 0
                
                if cached_version == current_version:
                    return cached_perms
    
    # Use repositories for database access
    admin_repo = AdminRepository(db)
    role_repo = RoleRepository(db)
    
    # Fetch admin record
    admin = await admin_repo.get_by_user_id(user.id)
    if not admin:
        return []
    
    # Fetch role
    role = await role_repo.get(admin.role_id)
    if not role:
        return []
    
    # Get current role version
    current_version = await get_cache(f"role:version:{role.id}")
    current_version = int(current_version) if current_version else 0

    # SUPER_ADMIN has all permissions
    if role.name == "SUPER_ADMIN":
        # Fetch all permissions from database to be explicit (ACID/Consistency)
        from app.modules.roles.repository import PermissionRepository
        perm_repo = PermissionRepository(db)
        all_perms = await perm_repo.list_all()
        permissions = [p.code for p in all_perms]
        
        # Cache with version
        to_cache = {
            "role_id": str(role.id),
            "role_version": current_version,
            "permissions": permissions
        }
        await set_cache(cache_key, to_cache, expire=300)
        return permissions
    
    # Fetch role permissions using repository
    permissions = await role_repo.get_permissions(role.id)
    permission_codes = [p.code for p in permissions]
    
    # Apply permission overrides if any
    if admin.permission_overrides:
        add_perms = admin.permission_overrides.get("add_permissions", [])
        remove_perms = admin.permission_overrides.get("remove_permissions", [])
        
        permission_codes.extend(add_perms)
        permission_codes = [p for p in permission_codes if p not in remove_perms]
    
    # Remove duplicates
    final_permissions = list(set(permission_codes))
    
    # Cache with version
    to_cache = {
        "role_id": str(role.id),
        "role_version": current_version,
        "permissions": final_permissions
    }
    await set_cache(cache_key, to_cache, expire=300)
    
    return final_permissions


def require_permissions(required_permissions: List[str]):
    """
    Dependency to check if user has required permissions.
    
    Args:
        required_permissions: List of required permission codes
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_verified_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Check if user has required permissions."""
        from app.core.exceptions import PermissionDeniedError
        from app.core.schemas.response import ErrorCode
        
        user_permissions = await get_user_permissions(current_user, db)
        
        # SUPER_ADMIN has all permissions
        if "*" in user_permissions:
            return current_user
        
        # Check if user has all required permissions
        for perm in required_permissions:
            if perm not in user_permissions:
                raise PermissionDeniedError(
                    error_code=ErrorCode.PERMISSION_DENIED,
                    message=f"Permission denied. Required: {', '.join(required_permissions)}"
                )
        
        return current_user
    
    return permission_checker


def require_admin():
    """Dependency to require admin role."""
    async def admin_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user is an admin."""
        from app.constants.enums import UserType
        from app.core.exceptions import PermissionDeniedError
        from app.core.schemas.response import ErrorCode
        
        if current_user.user_type != UserType.ADMIN:
            raise PermissionDeniedError(
                error_code=ErrorCode.PERMISSION_DENIED,
                message="Admin access required"
            )
        return current_user
    
    return admin_checker
