"""
Role and Permission management services.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from fastapi import Request

from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.roles.repository import RoleRepository, PermissionRepository
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.constants import ErrorCode
from app.modules.audit.service import audit_service
from app.modules.roles.schemas import (
    RoleResponse, 
    RoleDetailResponse, 
    RoleListItemResponse,
    RolesListResponse,
    PermissionResponse
)

class RoleService:
    """Service for role management business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)
    
    async def _invalidate_role_cache(self, role_id: UUID) -> None:
        """Increment role version to invalidate cached permissions for users."""
        from app.core.cache import increment_cache
        await increment_cache(f"role:version:{role_id}")

    async def create_role(
        self,
        name: str,
        actor_id: UUID,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
        request: Optional[Request] = None
    ) -> RoleResponse:
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
            details={
                "name": role.name, 
                "permission_ids": [str(p) for p in (permission_ids or [])]
            },
            request=request
        )
        
        return RoleResponse.model_validate(role)
    
    async def list_roles(
        self, 
        page: int = 1, 
        per_page: int = 20,
        name: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "created_at",
        order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List all roles with permission counts and pagination.
        """
        from sqlmodel import select, func
        from app.modules.roles.models import Role
        
        # Get total count
        count_query = select(func.count()).select_from(Role)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Use repository method for data access with pagination
        skip = (page - 1) * per_page
        roles_with_counts = await self.role_repo.list_with_permission_counts(
            skip=skip, 
            limit=per_page,
            filters={"name": name} if name else None,
            search_query=search,
            sort_by=sort,
            sort_order=order
        )
        
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        items = []
        for role, count in roles_with_counts:
            # We construct the response manually or use a specific schema that includes permission_count
            # RoleListItemResponse is designed for this but expects standard fields.
            # We can map it:
            item = RoleListItemResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                is_system=role.is_system,
                permissions_count=count,
                created_at=role.created_at,
                updated_at=role.updated_at
            )
            items.append(item)
            
        return {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    
    async def get_role(self, role_id: UUID) -> RoleDetailResponse:
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
        
        # Map to RoleDetailResponse
        # Use model_validate to handle the basic fields, then attach permissions
        
        # We need to construct the response manually because 'permissions' in the model
        # might expect a list of PermissionResponse/Permission objects.
        
        permission_responses = [
            PermissionResponse.model_validate(p) for p in permissions
        ]
        
        return RoleDetailResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            permissions=permission_responses,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    
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
                message="Cannot modify system roles",
                field="role_id"
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
        
        # Invalidate cache
        await self._invalidate_role_cache(role.id)
        
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
                message="Cannot delete system roles",
                field="role_id"
            )
        
        await self.role_repo.delete(str(role_id))
        
        # Invalidate cache
        await self._invalidate_role_cache(role.id)
        
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
    ) -> PermissionResponse:
        """
        Create a new permission.
        """
        from app.modules.roles.models import Permission

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
        
        return PermissionResponse.model_validate(permission)
    
    async def list_permissions(self) -> List[PermissionResponse]:
        """
        List all permissions.
        """
        permissions = await self.perm_repo.list_all()
        
        return [
            PermissionResponse.model_validate(p) for p in permissions
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
