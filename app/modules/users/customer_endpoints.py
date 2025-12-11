"""
Customer Management Endpoints.
"""
from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, status

from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.core.permissions import get_current_active_user
from app.core.docs import doc_responses
from app.modules.users.service import UserManagementService
from app.modules.users.schemas import CustomerCreate, CustomerUpdate, CustomerDetailResponse
from app.core.schemas.response import SuccessResponse, PaginatedResponse
from app.modules.users.models import User
from app.constants.enums import UserType

router = APIRouter(tags=["Customer Management"])

def check_super_admin(user: User):
    """Ensure user is an admin."""
    if user.user_type != UserType.ADMIN:
         from fastapi import HTTPException
         raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.post(
    "/",
    response_model=SuccessResponse[CustomerDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Customer",
    responses=doc_responses(
        success_message="Customer created successfully",
        success_status_code=status.HTTP_201_CREATED,
        errors=(401, 403, 409, 422)
    )
)
async def create_customer(
    data: CustomerCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new customer."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    customer = await service.create_customer(data, actor_id=current_user.id, request=request)
    return SuccessResponse(message="Customer created successfully", data=customer)

@router.get(
    "/",
    response_model=PaginatedResponse[CustomerDetailResponse],
    summary="List Customers",
    responses=doc_responses(
        success_message="Customers retrieved successfully",
        errors=(401, 403)
    )
)
async def list_customers(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str = Query(None, description="Search term"),
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    email: str = Query(None, description="Filter by email"),
    first_name: str = Query(None, description="Filter by first name"),
    is_active: bool = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List customers."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    
    # Construct filters dict
    filters = {}
    if email: filters["email"] = email
    if first_name: filters["first_name"] = first_name
    if is_active is not None: filters["is_active"] = is_active

    items, total = await service.list_customers(
        skip=skip, 
        limit=limit,
        filters=filters,
        search_query=q,
        sort_by=sort,
        sort_order=order
    )
    
    page = (skip // limit) + 1 if limit > 0 else 1
    return SuccessResponse(
        message="Customers retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "per_page": limit
        }
    )

@router.get(
    "/{customer_id}",
    response_model=SuccessResponse[CustomerDetailResponse],
    summary="Get Customer",
    responses=doc_responses(
        success_message="Customer retrieved successfully",
        errors=(401, 403, 404)
    )
)
async def get_customer(
    customer_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer details."""
    check_super_admin(current_user)
    service = UserManagementService(db)
    customer = await service.get_customer(customer_id)
    return SuccessResponse(message="Customer retrieved successfully", data=customer)

@router.put(
    "/{customer_id}",
    response_model=SuccessResponse[CustomerDetailResponse],
    summary="Update Customer",
    responses=doc_responses(
        success_message="Customer updated successfully",
        errors=(401, 403, 404, 422)
    )
)
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
    customer = await service.update_customer(customer_id, data, actor_id=current_user.id, request=request)
    return SuccessResponse(message="Customer updated successfully", data=customer)

@router.delete(
    "/{customer_id}",
    response_model=SuccessResponse[None],
    summary="Delete Customer",
    responses=doc_responses(
        success_message="Customer deleted successfully",
        errors=(401, 403, 404)
    )
)
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
    return SuccessResponse(message="Customer deleted successfully", data=None)
