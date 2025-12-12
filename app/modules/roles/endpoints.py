"""
Role management endpoints for RBAC.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.docs import doc_responses
from app.core.permissions import require_permissions
from app.modules.roles.schemas import RoleCreateRequest, RoleUpdateRequest, RoleResponse, RoleListItemResponse
from app.core.schemas.response import SuccessResponse, PaginatedResponse
from app.modules.roles.service import RoleService
from app.constants import PermissionEnum

router = APIRouter(tags=["Role Management"])


@router.post(
    "",
    response_model=SuccessResponse[RoleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Role",
    responses=doc_responses(
        success_message="Role created successfully",
        success_status_code=status.HTTP_201_CREATED,
        errors=(400, 401, 403, 409, 422)
    )
)
async def create_role(
    request: RoleCreateRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.ROLES_WRITE]))
):
    """
    Create a new role.
    
    - Requires `roles:write` permission
    - Role name must be unique
    - Can assign permissions during creation
    - System roles cannot be created via API
    """
    role_service = RoleService(db)
    role_data = await role_service.create_role(
        name=request.name,
        description=request.description,
        permission_ids=request.permission_ids,
        actor_id=current_user.id,
        request=req
    )
    
    return SuccessResponse(
        message="Role created successfully",
        data=role_data
    )


@router.get(
    "",
    response_model=PaginatedResponse[RoleListItemResponse],
    summary="List Roles",
    responses=doc_responses(
        success_message="Roles retrieved successfully",
        errors=(401, 403)
    )
)
async def list_roles(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    name: str = Query(None, description="Filter by role name"),
    q: str = Query(None, description="Search term"),
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.ROLES_READ]))
):
    """
    List all roles with pagination.
    
    - Requires `roles:read` permission
    - Returns role summary without full permission details
    - Returns paginated results with metadata
    """
    role_service = RoleService(db)
    role_data = await role_service.list_roles(
        page=page, 
        per_page=per_page,
        name=name,
        search=q,
        sort=sort,
        order=order
    )
    
    return SuccessResponse(
        message="Roles retrieved successfully",
        data=role_data
    )


@router.get(
    "/{role_id}",
    response_model=SuccessResponse,
    summary="Get Role Details",
    responses=doc_responses(
        success_example={"id": "550e8400-e29b-41d4-a716-446655440000", "name": "MANAGER", "permissions": []},
        success_message="Role retrieved successfully",
        errors=(401, 403, 404)
    )
)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.ROLES_READ]))
):
    """
    Get role details with permissions.
    
    - Requires `roles:read` permission
    - Returns full role details including all permissions
    """
    role_service = RoleService(db)
    role_data = await role_service.get_role(role_id)
    
    return SuccessResponse(
        message="Role retrieved successfully",
        data=role_data
    )


@router.put(
    "/{role_id}",
    response_model=SuccessResponse,
    summary="Update Role",
    responses=doc_responses(
        success_example=None,
        success_message="Role updated successfully",
        errors=(400, 401, 403, 404, 422)
    )
)
async def update_role(
    role_id: UUID,
    request: RoleUpdateRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.ROLES_WRITE]))
):
    """
    Update role details and permissions.
    
    - Requires `roles:write` permission
    - Cannot modify system roles
    - Can update name, description, and permissions
    """
    role_service = RoleService(db)
    await role_service.update_role(
        role_id=role_id,
        name=request.name,
        description=request.description,
        permission_ids=request.permission_ids,
        actor_id=current_user.id,
        request=req
    )
    
    return SuccessResponse(
        message="Role updated successfully",
        data=None
    )


@router.delete(
    "/{role_id}",
    response_model=SuccessResponse,
    summary="Delete Role",
    responses=doc_responses(
        success_example=None,
        success_message="Role deleted successfully",
        errors=(400, 401, 403, 404)
    )
)
async def delete_role(
    role_id: UUID,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.ROLES_DELETE]))
):
    """
    Delete a role.
    
    - Requires `roles:delete` permission
    - Cannot delete system roles
    - Cannot delete roles that are assigned to users
    """
    role_service = RoleService(db)
    await role_service.delete_role(
        role_id=role_id,
        actor_id=current_user.id,
        request=req
    )
    
    return SuccessResponse(
        message="Role deleted successfully",
        data=None
    )
