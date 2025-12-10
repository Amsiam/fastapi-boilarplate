"""
Customer Management Endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, status

from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.permissions import get_current_active_user
from app.services.user_management_service import UserManagementService
from app.schemas.user import CustomerCreate, CustomerUpdate, CustomerDetailResponse
from app.models.user import User
from app.constants.enums import UserRole
from app.schemas.pagination import PaginatedResponse

router = APIRouter(tags=["Customer Management"])

def check_super_admin(user: User):
    """Ensure user is an admin."""
    if user.role != UserRole.ADMIN:
         from fastapi import HTTPException
         raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.post("/", response_model=CustomerDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new customer."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    return await service.create_customer(data, actor_id=current_user.id, request=request)

@router.get("/", response_model=PaginatedResponse[CustomerDetailResponse])
async def list_customers(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List customers."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    items, total = await service.list_customers(skip, limit)
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit
    )

@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer details."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    return await service.get_customer(customer_id)

@router.put("/{customer_id}", response_model=CustomerDetailResponse)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update customer."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    return await service.update_customer(customer_id, data, actor_id=current_user.id, request=request)

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete customer."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    await service.delete_customer(customer_id, actor_id=current_user.id, request=request)
