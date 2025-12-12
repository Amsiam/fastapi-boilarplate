"""
Role and Permission schemas.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============= Request Schemas =============

class RoleCreateRequest(BaseModel):
    """Create role request."""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: list[UUID] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    """Update role request."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: Optional[list[UUID]] = None


class PermissionCreateRequest(BaseModel):
    """Create permission request."""
    code: str = Field(min_length=1, max_length=100, pattern="^[a-z_]+:[a-z_]+$")
    description: Optional[str] = Field(None, max_length=500)
    resource: str = Field(min_length=1, max_length=50)
    action: str = Field(min_length=1, max_length=50)


class AssignRoleRequest(BaseModel):
    """Assign role to admin request."""
    role_id: UUID


class OverridePermissionsRequest(BaseModel):
    """Override admin permissions request."""
    add_permissions: list[str] = Field(default_factory=list)
    remove_permissions: list[str] = Field(default_factory=list)


# ============= Response Schemas =============

class PermissionResponse(BaseModel):
    """Permission response."""
    id: UUID
    code: str
    description: Optional[str]
    resource: Optional[str]
    action: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    """Role response."""
    id: UUID
    name: str
    description: Optional[str]
    is_system: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleDetailResponse(BaseModel):
    """Detailed role response with permissions."""
    id: UUID
    name: str
    description: Optional[str]
    is_system: bool
    permissions: list[PermissionResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleListItemResponse(BaseModel):
    """Role list item response."""
    id: UUID
    name: str
    description: Optional[str]
    is_system: bool
    permissions_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RolesListResponse(BaseModel):
    """List of roles response."""
    roles: list[RoleListItemResponse]


class PermissionsListResponse(BaseModel):
    """List of permissions response."""
    permissions: list[PermissionResponse]
