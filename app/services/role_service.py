"""
Role and Permission management services.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import Request

from sqlmodel.ext.asyncio.session import AsyncSession

from app.repositories import RoleRepository, PermissionRepository
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.constants import ErrorCode
from app.services.audit_service import audit_service


class RoleService:
    """Service for role management business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)
    
    async def create_role(
        self,
        name: str,
        actor_id: UUID,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
        request: Optional[Request] = None
    ) -> dict:
        """
        Create a new role.
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
        
        await audit_service.log_action(
            action="create_role",
            actor_id=actor_id,
            target_id=str(role.id),
            target_type="role",
            details={"name": role.name, "permission_ids": [str(p) for p in (permission_ids or [])]},
            request=request
        )
        
        return {"id": str(role.id), "name": role.name}
    
    async def list_roles(self, page: int = 1, per_page: int = 20) -> dict:
        """
        List all roles with permission counts and pagination.
        """
        from sqlmodel import select, func
        from app.models.role import Role
        
        # Get total count
        count_query = select(func.count()).select_from(Role)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Use repository method for data access with pagination
        skip = (page - 1) * per_page
        roles_with_counts = await self.role_repo.list_with_permission_counts(
            skip=skip, limit=per_page
        )
        
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        return {
            "items": [
                {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                    "is_system_role": role.is_system,
                    "permission_count": count,
                    "created_at": role.created_at.isoformat()
                }
                for role, count in roles_with_counts
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    
    async def get_role(self, role_id: UUID) -> dict:
        """
        Get role details with permissions.
        """
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
        actor_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
        request: Optional[Request] = None
    ) -> None:
        """
        Update role details and permissions.
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
        
        old_values = {
            "name": role.name,
            "description": role.description
        }
        
        # Update role
        await self.role_repo.update_role(
            role_id=role.id,
            name=name,
            description=description,
            permission_ids=permission_ids
        )
        
        new_values = {}
        if name: new_values["name"] = name
        if description: new_values["description"] = description
        if permission_ids: new_values["permission_ids"] = [str(p) for p in permission_ids]
        
        await audit_service.log_action(
            action="update_role",
            actor_id=actor_id,
            target_id=str(role.id),
            target_type="role",
            old_values=old_values,
            new_values=new_values,
            request=request
        )
    
    async def delete_role(self, role_id: UUID, actor_id: UUID, request: Optional[Request] = None) -> None:
        """
        Delete a role.
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
        
        await self.role_repo.delete(str(role_id))
        
        await audit_service.log_action(
            action="delete_role",
            actor_id=actor_id,
            target_id=str(role.id),
            target_type="role",
            details={"name": role.name},
            request=request
        )


class PermissionService:
    """Service for permission management business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.perm_repo = PermissionRepository(db)
    
    async def create_permission(
        self, 
        code: str, 
        actor_id: UUID,
        description: Optional[str] = None,
        request: Optional[Request] = None
    ) -> dict:
        """
        Create a new permission.
        """
        from app.models.role import Permission

        # Check if permission already exists
        existing = await self.perm_repo.get_by_code(code)
        if existing:
            raise ConflictError(
                error_code=ErrorCode.PERMISSION_ALREADY_EXISTS,
                message=f"Permission '{code}' already exists"
            )
        
        # Create permission
        permission = Permission(
            code=code,
            description=description or ""
        )
        permission = await self.perm_repo.create(permission)
        
        await audit_service.log_action(
            action="create_permission",
            actor_id=actor_id,
            target_id=str(permission.id),
            target_type="permission",
            details={"code": permission.code},
            request=request
        )
        
        return {"id": str(permission.id), "code": permission.code}
    
    async def list_permissions(self) -> List[dict]:
        """
        List all permissions.
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
    
    async def delete_permission(self, permission_id: UUID, actor_id: UUID, request: Optional[Request] = None) -> None:
        """
        Delete a permission.
        """
        permission = await self.perm_repo.get(str(permission_id))
        
        if not permission:
            raise NotFoundError(
                error_code=ErrorCode.PERMISSION_NOT_FOUND,
                message="Permission not found"
            )
        
        await self.perm_repo.delete(str(permission_id))
        
        await audit_service.log_action(
            action="delete_permission",
            actor_id=actor_id,
            target_id=str(permission.id),
            target_type="permission",
            details={"code": permission.code},
            request=request
        )
