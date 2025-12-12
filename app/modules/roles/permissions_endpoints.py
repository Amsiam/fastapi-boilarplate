"""
Permission management endpoints for RBAC.

NOTE: Permissions are typically predefined in the system via constants.
These CRUD endpoints are deprecated and may be removed in future versions.
Use the list endpoint to view available permissions for role assignment.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.docs import doc_responses
from app.core.permissions import require_permissions
from typing import List
from app.modules.roles.schemas import PermissionCreateRequest, PermissionResponse
from app.core.schemas.response import SuccessResponse, PaginatedResponse
from app.modules.roles.service import PermissionService
from app.constants import PermissionEnum

router = APIRouter(tags=["Permission Management"])


@router.get(
    "",
    response_model=SuccessResponse[List[PermissionResponse]],
    summary="List Permissions",
    responses=doc_responses(
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


# NOTE: Create and Delete permission endpoints are deprecated.
# Permissions should be defined in app/constants/permissions.py and seeded.
# These endpoints are kept for backwards compatibility but may be removed.

# @router.post(
#     "",
#     response_model=SuccessResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create Permission (Deprecated)",
#     deprecated=True,
# )
# async def create_permission(...):
#     """Deprecated: Permissions should be predefined in constants."""
#     pass

# @router.delete(
#     "/{permission_id}",
#     response_model=SuccessResponse,
#     summary="Delete Permission (Deprecated)",
#     deprecated=True,
# )
# async def delete_permission(...):
#     """Deprecated: Permissions should be predefined in constants."""
#     pass
