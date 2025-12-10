"""
Permission management endpoints for RBAC.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.docs import doc_responses
from app.core.permissions import require_permissions
from app.schemas.role import PermissionCreateRequest
from app.schemas.response import SuccessResponse
from app.services import PermissionService
from app.constants import PermissionEnum

router = APIRouter(tags=["Permission Management"])


@router.post(
    "",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Permission",
    responses=doc_responses(
        success_example={"id": "550e8400-e29b-41d4-a716-446655440000", "code": "custom:action"},
        success_message="Permission created successfully",
        errors=(401, 403, 409, 422)
    )
)
async def create_permission(
    request: PermissionCreateRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.PERMISSIONS_WRITE]))
):
    """
    Create a new permission.
    
    - Requires `permissions:write` permission
    - Permission code must be unique
    - Code format: `resource:action` (e.g., `orders:read`)
    """
    perm_service = PermissionService(db)
    perm_data = await perm_service.create_permission(
        code=request.code,
        description=request.description,
        actor_id=current_user.id,
        request=req
    )
    
    return SuccessResponse(
        message="Permission created successfully",
        data=perm_data
    )


@router.get(
    "",
    response_model=SuccessResponse,
    summary="List Permissions",
    responses=doc_responses(
        success_example=[{"id": "550e8400-e29b-41d4-a716-446655440000", "code": "users:read", "description": "View users"}],
        success_message="Permissions retrieved successfully",
        errors=(401, 403)
    )
)
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.PERMISSIONS_READ]))
):
    """
    List all permissions.
    
    - Requires `permissions:read` permission
    - Returns all available permissions in the system
    """
    perm_service = PermissionService(db)
    perm_data = await perm_service.list_permissions()
    
    return SuccessResponse(
        message="Permissions retrieved successfully",
        data=perm_data
    )


@router.delete(
    "/{permission_id}",
    response_model=SuccessResponse,
    summary="Delete Permission",
    responses=doc_responses(
        success_example=None,
        success_message="Permission deleted successfully",
        errors=(401, 403, 404)
    )
)
async def delete_permission(
    permission_id: UUID,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.PERMISSIONS_DELETE]))
):
    """
    Delete a permission.
    
    - Requires `permissions:delete` permission
    - Will remove permission from all roles
    """
    perm_service = PermissionService(db)
    await perm_service.delete_permission(
        permission_id=permission_id,
        actor_id=current_user.id,
        request=req
    )
    
    return SuccessResponse(
        message="Permission deleted successfully",
        data=None
    )
