"""
Admin Management Endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, status

from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.permissions import get_current_active_user
from app.core.docs import doc_responses
from app.modules.users.service import UserManagementService
from app.modules.users.schemas import AdminCreate, AdminUpdate, AdminDetailResponse
from app.core.schemas.response import SuccessResponse
from app.modules.users.models import User
from app.constants.enums import UserRole

router = APIRouter(tags=["Admin Management"])

def check_super_admin(user: User):
    """Ensure user is an admin."""
    if user.role != UserRole.ADMIN:
         from fastapi import HTTPException
         raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.post(
    "/",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Admin",
    responses=doc_responses(
        success_example={"id": "550e8400-e29b-41d4-a716-446655440000", "email": "admin@example.com"},
        success_message="Admin created successfully",
        errors=(401, 403, 409, 422)
    )
)
async def create_admin(
    data: AdminCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new admin."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    admin = await service.create_admin(data, actor_id=current_user.id, request=request)
    return SuccessResponse(message="Admin created successfully", data=admin)

@router.get(
    "/",
    response_model=SuccessResponse,
    summary="List Admins",
    responses=doc_responses(
        success_example={"items": [{"id": "...", "email": "admin@example.com"}], "total": 1, "page": 1},
        success_message="Admins retrieved successfully",
        errors=(401, 403)
    )
)
async def list_admins(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List admins."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    items, total = await service.list_admins(skip, limit)
    
    page = (skip // limit) + 1 if limit > 0 else 1
    return SuccessResponse(
        message="Admins retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "per_page": limit
        }
    )

@router.get(
    "/{admin_id}",
    response_model=SuccessResponse,
    summary="Get Admin",
    responses=doc_responses(
        success_example={"id": "550e8400-e29b-41d4-a716-446655440000", "email": "admin@example.com"},
        success_message="Admin retrieved successfully",
        errors=(401, 403, 404)
    )
)
async def get_admin(
    admin_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin details."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    admin = await service.get_admin(admin_id)
    return SuccessResponse(message="Admin retrieved successfully", data=admin)

@router.put(
    "/{admin_id}",
    response_model=SuccessResponse,
    summary="Update Admin",
    responses=doc_responses(
        success_example={"id": "550e8400-e29b-41d4-a716-446655440000", "email": "admin@example.com"},
        success_message="Admin updated successfully",
        errors=(401, 403, 404, 422)
    )
)
async def update_admin(
    admin_id: UUID,
    data: AdminUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update admin."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    admin = await service.update_admin(admin_id, data, actor_id=current_user.id, request=request)
    return SuccessResponse(message="Admin updated successfully", data=admin)

@router.delete(
    "/{admin_id}",
    response_model=SuccessResponse,
    summary="Delete Admin",
    responses=doc_responses(
        success_example=None,
        success_message="Admin deleted successfully",
        errors=(401, 403, 404)
    )
)
async def delete_admin(
    admin_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete admin."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    await service.delete_admin(admin_id, actor_id=current_user.id, request=request)
    return SuccessResponse(message="Admin deleted successfully", data=None)
