"""
Role and Permission management services.
"""
from typing import List, Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.repositories import RoleRepository, PermissionRepository
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.constants import ErrorCode


class RoleService:
    """Service for role management business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)
    
    async def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None
    ) -> dict:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            permission_ids: List of permission IDs to assign
            
        Returns:
            Created role data
            
        Raises:
            ConflictError: If role already exists
        """
        # Check if role already exists
        existing = await self.role_repo.get_by_name(name)
        if existing:
            raise ConflictError(
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                message=f"Role '{name}' already exists"
            )
        
        # Create role
        role = await self.role_repo.create_role(
            name=name,
            description=description,
            permission_ids=permission_ids
        )
        
        return {"id": str(role.id), "name": role.name}
    
    async def list_roles(self) -> List[dict]:
        """
        List all roles with permission counts.
        
        Returns:
            List of role data with permission counts
        """
        # Use repository method for data access
        roles_with_counts = await self.role_repo.list_with_permission_counts()
        
        return [
            {
                "id": str(role.id),
                "name": role.name,
                "description": role.description,
                "is_system_role": role.is_system,
                "permission_count": count,
                "created_at": role.created_at.isoformat()
            }
            for role, count in roles_with_counts
        ]
    
    async def get_role(self, role_id: UUID) -> dict:
        """
        Get role details with permissions.
        
        Args:
            role_id: Role ID
            
        Returns:
            Role data with permissions
            
        Raises:
            NotFoundError: If role not found
        """
        # Use eager loading to get role and permissions in fewer queries
        result = await self.role_repo.get_with_permissions(role_id)
        
        if not result:
            raise NotFoundError(
                error_code=ErrorCode.ROLE_NOT_FOUND,
                message="Role not found"
            )
        
        role, permissions = result
        
        return {
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system,
            "permissions": [
                {"id": str(p.id), "code": p.code, "description": p.description}
                for p in permissions
            ],
            "created_at": role.created_at.isoformat()
        }
    
    async def update_role(
        self,
        role_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None
    ) -> None:
        """
        Update role details and permissions.
        
        Args:
            role_id: Role ID
            name: New role name
            description: New description
            permission_ids: New permission IDs
            
        Raises:
            NotFoundError: If role not found
            ValidationError: If trying to modify system role
        """
        role = await self.role_repo.get(str(role_id))
        
        if not role:
            raise NotFoundError(
                error_code=ErrorCode.ROLE_NOT_FOUND,
                message="Role not found"
            )
        
        if role.is_system:
            raise ValidationError(
                error_code=ErrorCode.CANNOT_MODIFY_SYSTEM_ROLE,
                message="Cannot modify system roles"
            )
        
        # Update role
        await self.role_repo.update_role(
            role_id=role.id,
            name=name,
            description=description,
            permission_ids=permission_ids
        )
    
    async def delete_role(self, role_id: UUID) -> None:
        """
        Delete a role.
        
        Args:
            role_id: Role ID
            
        Raises:
            NotFoundError: If role not found
            ValidationError: If trying to delete system role
        """
        role = await self.role_repo.get(str(role_id))
        
        if not role:
            raise NotFoundError(
                error_code=ErrorCode.ROLE_NOT_FOUND,
                message="Role not found"
            )
        
        if role.is_system:
            raise ValidationError(
                error_code=ErrorCode.CANNOT_MODIFY_SYSTEM_ROLE,
                message="Cannot delete system roles"
            )
        
        # TODO: Check if role is in use by any admins
        
        await self.role_repo.delete(str(role_id))


class PermissionService:
    """Service for permission management business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.perm_repo = PermissionRepository(db)
    
    async def create_permission(self, code: str, description: Optional[str] = None) -> dict:
        """
        Create a new permission.
        
        Args:
            code: Permission code
            description: Permission description
            
        Returns:
            Created permission data
            
        Raises:
            ConflictError: If permission already exists
        """
        # Check if permission already exists
        existing = await self.perm_repo.get_by_code(code)
        if existing:
            raise ConflictError(
                error_code=ErrorCode.PERMISSION_ALREADY_EXISTS,
                message=f"Permission '{code}' already exists"
            )
        
        # Create permission
        permission = await self.perm_repo.create(
            code=code,
            description=description
        )
        
        return {"id": str(permission.id), "code": permission.code}
    
    async def list_permissions(self) -> List[dict]:
        """
        List all permissions.
        
        Returns:
            List of permission data
        """
        permissions = await self.perm_repo.list_all()
        
        return [
            {
                "id": str(p.id),
                "code": p.code,
                "description": p.description,
                "created_at": p.created_at.isoformat()
            }
            for p in permissions
        ]
    
    async def delete_permission(self, permission_id: UUID) -> None:
        """
        Delete a permission.
        
        Args:
            permission_id: Permission ID
            
        Raises:
            NotFoundError: If permission not found
        """
        permission = await self.perm_repo.get(str(permission_id))
        
        if not permission:
            raise NotFoundError(
                error_code=ErrorCode.PERMISSION_NOT_FOUND,
                message="Permission not found"
            )
        
        await self.perm_repo.delete(str(permission_id))
