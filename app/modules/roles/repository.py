"""
Role and Permission repositories.
"""
from typing import List, Optional
from uuid import UUID

from sqlmodel import select, func, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.roles.models import Role, Permission, RolePermission
from app.core.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repository for Role model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return await self.get_by_field("name", name)
    
    async def get_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions for a role."""
        result = await self.db.execute(
            select(Permission)
            .join(RolePermission)
            .where(RolePermission.role_id == role_id)
        )
        return list(result.scalars().all())
    
    async def get_with_permissions(self, role_id: UUID) -> Optional[tuple[Role, List[Permission]]]:
        """
        Get role with permissions in a single query (eager loading).
        Returns tuple of (role, permissions) to avoid N+1 queries.
        """
        # Get role
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            return None
        
        # Get permissions in single query
        permissions = await self.get_permissions(role_id)
        
        return (role, permissions)
    
    async def list_with_permission_counts(
        self, 
        skip: int = 0, 
        limit: int = 20,
        filters: Optional[dict] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[tuple[Role, int]]:
        """
        Get all roles with their permission counts.
        Optimized to avoid N+1 queries using a single JOIN and GROUP BY.
        
        Returns:
            List of tuples (role, permission_count)
        """
        from app.core.filtering import apply_filters, apply_search, apply_sorting, SortOrder

        query = select(
            Role,
            func.count(RolePermission.permission_id).label("permission_count")
        ).outerjoin(RolePermission, Role.id == RolePermission.role_id)

        # Apply Filters
        if filters:
            query = apply_filters(query, Role, filters)
        
        # Apply Search
        if search_query:
            # Search in name and description
            query = apply_search(query, Role, search_query, ["name", "description"])

        query = query.group_by(Role.id)

        # Apply Sorting
        query = apply_sorting(query, Role, sort_by, SortOrder(sort_order))

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        
        return result.all()
    
    async def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None
    ) -> Role:
        """
        Create a role with permissions.
        Optimized with batch insert for permissions.
        """
        from uuid import uuid4
        
        role = Role(
            id=uuid4(),
            name=name,
            description=description,
            is_system=False  # Default to False
        )
        self.db.add(role)
        await self.db.flush()  # Get role ID
        
        # Batch insert permissions (single query instead of N queries)
        if permission_ids:
            role_perms = [
                RolePermission(role_id=role.id, permission_id=perm_id)
                for perm_id in permission_ids
            ]
            self.db.add_all(role_perms)  # Batch insert
        
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def update_role(
        self,
        role_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None
    ) -> Optional[Role]:
        """
        Update a role and its permissions.
        Optimized with batch operations.
        """
        role = await self.get(role_id)
        if not role:
            return None
        
        # Update basic fields
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        
        # Update permissions if provided
        if permission_ids is not None:
            # Batch delete all existing permissions (single DELETE query)
            await self.db.execute(
                delete(RolePermission).where(RolePermission.role_id == role_id)
            )
            
            # Batch insert new permissions (single INSERT query)
            if permission_ids:
                role_perms = [
                    RolePermission(role_id=role_id, permission_id=perm_id)
                    for perm_id in permission_ids
                ]
                self.db.add_all(role_perms)
        
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def add_permission(self, role_id: UUID, permission_id: UUID) -> RolePermission:
        """Add a permission to a role."""
        role_perm = RolePermission(role_id=role_id, permission_id=permission_id)
        self.db.add(role_perm)
        await self.db.commit()
        return role_perm
    
    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """Remove a permission from a role."""
        result = await self.db.execute(
            select(RolePermission)
            .where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            )
        )
        role_perm = result.scalar_one_or_none()
        if role_perm:
            await self.db.delete(role_perm)
            await self.db.commit()
            return True
        return False


class PermissionRepository(BaseRepository[Permission]):
    """Repository for Permission model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Permission, db)
    
    async def get_by_code(self, code: str) -> Optional[Permission]:
        """Get permission by code."""
        return await self.get_by_field("code", code)
    
    async def get_by_resource(self, resource: str) -> List[Permission]:
        """Get all permissions for a resource."""
        result = await self.db.execute(
            select(Permission).where(Permission.resource == resource)
        )
        return result.scalars().all()
    
    async def list_all(self) -> List[Permission]:
        """Get all permissions."""
        result = await self.db.execute(select(Permission))
        return result.scalars().all()
