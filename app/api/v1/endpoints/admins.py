"""
Admin Management Endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, status

from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.permissions import get_current_active_user
from app.services.user_management_service import UserManagementService
from app.schemas.user import AdminCreate, AdminUpdate, AdminDetailResponse
from app.models.user import User
from app.constants.enums import UserRole
from app.schemas.pagination import PaginatedResponse

router = APIRouter(tags=["Admin Management"])

def check_super_admin(user: User):
    """Ensure user is an admin."""
    # Ideally should check specific permission or super admin flag
    # For now, any ADMIN can manage.
    if user.role != UserRole.ADMIN:
         from fastapi import HTTPException
         raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.post("/", response_model=AdminDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    data: AdminCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new admin."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    return await service.create_admin(data, actor_id=current_user.id, request=request)

@router.get("/", response_model=PaginatedResponse[AdminDetailResponse])
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
    
    # Construct pagination links
    # Assuming standard structure manually or via schema helper
    # PaginatedResponse expects data, total, page, size, etc.
    # Let's verify PaginatedResponse structure.
    # It usually expects generic T.
    
    # Create paginated response
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit
    )

@router.get("/{admin_id}", response_model=AdminDetailResponse)
async def get_admin(
    admin_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin details."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    return await service.get_admin(admin_id)

@router.put("/{admin_id}", response_model=AdminDetailResponse)
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
    return await service.update_admin(admin_id, data, actor_id=current_user.id, request=request)

@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
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
