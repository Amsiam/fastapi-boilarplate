
"""
User Management Service for Admins and Customers.
Handles CRUD operations, Soft Deletes, and Audit Logging.
"""
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from fastapi import Request

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func, or_, col

from app.core.security import get_password_hash
from app.modules.users.models import User, Admin, Customer
from app.constants.enums import UserType
from app.modules.users.repository import UserRepository, AdminRepository, CustomerRepository
from app.modules.roles.repository import RoleRepository
from app.modules.audit.service import audit_service
from app.modules.users.schemas import (
    AdminCreate, AdminUpdate, AdminDetailResponse,
    CustomerCreate, CustomerUpdate, CustomerDetailResponse
)
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.constants import ErrorCode
from app.modules.roles.models import Role


class UserManagementService:
    """Service for managing Admins and Customers."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.admin_repo = AdminRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.role_repo = RoleRepository(session)

    async def _check_email_exists(self, email: str):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError(
                error_code=ErrorCode.USER_ALREADY_EXISTS,
                message=f"User with email {email} already exists"
            )

    # ================= ADMIN MANAGEMENT =================

    async def create_admin(self, data: AdminCreate, actor_id: UUID, request: Optional[Request] = None) -> AdminDetailResponse:
        """Create a new admin user."""
        await self._check_email_exists(data.email)

        # 1. Resolve Role
        if data.role_id:
            role = await self.role_repo.get(data.role_id)
            if not role:
                 raise NotFoundError(error_code=ErrorCode.ROLE_NOT_FOUND, message="Role not found")
        else:
            role = await self.role_repo.get_by_name("ADMIN")
            if not role:
                 # Seed it if missing (simplifies testing too)
                 role = Role(name="ADMIN", description="Administrator", is_system=True)
                 role = await self.role_repo.create(role)

        # 2. Create User
        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            user_type=UserType.ADMIN,
            is_active=True,
            is_verified=True
        )
        user = await self.user_repo.create(user)

        # 3. Create Admin Profile
        admin = Admin(
            user_id=user.id,
            username=data.username,
            role_id=role.id
        )
        admin = await self.admin_repo.create(admin)

        # 4. Audit Log
        await audit_service.log_action(
            action="create_admin",
            actor_id=actor_id,
            target_id=str(admin.id),
            target_type="admin",
            details={"email": data.email, "username": data.username},
            request=request
        )
        
        return AdminDetailResponse(
            id=admin.id,
            user_id=user.id,
            email=user.email,
            username=admin.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def list_admins(
        self, 
        skip: int = 0, 
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[AdminDetailResponse], int]:
        """List admins with pagination, filtering, searching and sorting."""
        from app.core.filtering import apply_filters, apply_sorting, apply_search
        
        # Base query
        query = select(Admin, User).join(User).where(User.deleted_at == None)
        
        # Apply filters
        if filters:
            user_filters = {}
            admin_filters = {}
            
            for k, v in filters.items():
                if hasattr(User, k.split("__")[0]):
                    user_filters[k] = v
                elif hasattr(Admin, k.split("__")[0]):
                    admin_filters[k] = v
                    
            if user_filters:
                query = apply_filters(query, User, user_filters)
            if admin_filters:
                query = apply_filters(query, Admin, admin_filters)

        # Apply Search
        if search_query:
            # Search across User.email, Admin.username
            query = apply_search(query, User, search_query, ["email"])
            # We want OR condition across tables. apply_search does OR within model.
            # Custom search for joined tables:
            from sqlmodel import or_, col
            query = query.where(
                or_(
                    col(User.email).ilike(f"%{search_query}%"),
                    col(Admin.username).ilike(f"%{search_query}%")
                )
            )

        # Apply Sorting
        if hasattr(User, sort_by):
            query = apply_sorting(query, User, sort_by, sort_order)
        elif hasattr(Admin, sort_by):
            query = apply_sorting(query, Admin, sort_by, sort_order)
        else:
            # Default to User.created_at
            query = apply_sorting(query, User, "created_at", sort_order)
            
        # Get total count (inefficient but simple for now: wrap subquery)
        # For accurate count with filters, we need to count the results of the filtered query
        # But `count_query` needs to be separate.
        # Simplest: execute count on the filtered query without limit/offset? 
        # Or duplicate logic. Duplicating logic is safer for SQLModel.
        
        # Re-construct query for count or use subquery
        from sqlalchemy import func
        count_subquery = query.subquery()
        count_query = select(func.count()).select_from(count_subquery)
        
        total = (await self.session.execute(count_query)).scalar_one()
        
        # Apply pagination
        result = await self.session.execute(query.offset(skip).limit(limit))
        rows = result.all()
        
        admins = []
        for admin, user in rows:
            admins.append(AdminDetailResponse(
                id=admin.id,
                user_id=user.id,
                email=user.email,
                username=admin.username,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at
            ))
            
        return admins, total

    async def get_admin(self, admin_id: UUID) -> AdminDetailResponse:
        """Get admin by ID."""
        query = select(Admin, User).join(User).where(
            (Admin.id == admin_id) & (User.deleted_at == None)
        )
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="Admin not found")
            
        admin, user = row
        return AdminDetailResponse(
            id=admin.id,
            user_id=user.id,
            email=user.email,
            username=admin.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def update_admin(self, admin_id: UUID, data: AdminUpdate, actor_id: UUID, request: Optional[Request] = None) -> AdminDetailResponse:
        """Update admin."""
        # Check existence
        admin = await self.admin_repo.get(admin_id)
        if not admin:
             raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="Admin not found")
        
        # Protect super admin from editing (except password)
        if admin.is_super_admin:
            raise PermissionDeniedError(
                error_code=ErrorCode.PERMISSION_DENIED,
                message="Super admin cannot be edited. Use change password route instead."
            )
        
        user = await self.user_repo.get(admin.user_id)

        old_values = {
            "email": user.email,
            "username": admin.username,
            "is_active": user.is_active
        }

        # Update User fields
        user_updates = {}
        if data.email and data.email != user.email:
            existing = await self.user_repo.get_by_email(data.email)
            if existing and existing.id != user.id:
                 raise ConflictError(error_code=ErrorCode.USER_ALREADY_EXISTS, message="Email already in use")
            user_updates["email"] = data.email
            
        if data.password:
            user_updates["hashed_password"] = get_password_hash(data.password)
            
        if data.is_active is not None:
            user_updates["is_active"] = data.is_active

        if user_updates:
            await self.user_repo.update(user, user_updates)

        # Update Admin fields
        admin_updates = {}
        if data.username:
            admin_updates["username"] = data.username
            
        if admin_updates:
            await self.admin_repo.update(admin, admin_updates)
            
        # Invalidate Cache
        from app.core.cache import delete_cache, user_profile_key
        await delete_cache(user_profile_key(str(user.id)))

        # Audit
        new_values = {
            "email": user.email,
            "username": admin.username,
            "is_active": user.is_active
        }
        await audit_service.log_action(
            action="update_admin",
            actor_id=actor_id,
            target_id=str(admin.id),
            target_type="admin",
            old_values=old_values,
            new_values=new_values,
            request=request
        )

        # Return updated
        return await self.get_admin(admin_id) # Reuse get logic for simplicity

    async def delete_admin(self, admin_id: UUID, actor_id: UUID, request: Optional[Request] = None):
        """Soft delete admin."""
        admin = await self.admin_repo.get(admin_id)
        if not admin:
             raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="Admin not found")
        
        # Protect super admin from deletion
        if admin.is_super_admin:
            raise PermissionDeniedError(
                error_code=ErrorCode.PERMISSION_DENIED,
                message="Super admin cannot be deleted."
            )
             
        success = await self.user_repo.soft_delete(admin.user_id)
        if not success:
             raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="User not found")
             
        # Invalidate Cache
        from app.core.cache import delete_cache, user_profile_key
        await delete_cache(user_profile_key(str(admin.user_id)))
             
        await audit_service.log_action(
            action="delete_admin",
            actor_id=actor_id,
            target_id=str(admin.id),
            target_type="admin",
            details={"user_id": str(admin.user_id)},
            request=request
        )

    # ================= CUSTOMER MANAGEMENT =================

    async def create_customer(self, data: CustomerCreate, actor_id: UUID, request: Optional[Request] = None) -> CustomerDetailResponse:
        """Create a new customer."""
        await self._check_email_exists(data.email)

        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            user_type=UserType.CUSTOMER,
            is_active=True,
            is_verified=True
        )
        user = await self.user_repo.create(user)

        customer = Customer(
            user_id=user.id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number
        )
        customer = await self.customer_repo.create(customer)

        await audit_service.log_action(
            action="create_customer",
            actor_id=actor_id,
            target_id=str(customer.id),
            target_type="customer",
            details={"email": data.email, "name": f"{data.first_name} {data.last_name}"},
            request=request
        )
        
        return CustomerDetailResponse(
            id=customer.id,
            user_id=user.id,
            email=user.email,
            first_name=customer.first_name,
            last_name=customer.last_name,
            phone_number=customer.phone_number,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def list_customers(
        self, 
        skip: int = 0, 
        limit: int = 20,
        filters: Optional[dict] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[CustomerDetailResponse], int]:
        """List customers with pagination."""
        from app.core.filtering import apply_filters, apply_sorting, SortOrder
        from sqlmodel import or_, col

        query = select(Customer, User).join(User).where(User.deleted_at == None)

        if filters:
            # Apply filters to User model (e.g. email, is_active)
            query = apply_filters(query, User, filters)
            # Apply filters to Customer model (e.g. first_name)
            query = apply_filters(query, Customer, filters)

        if search_query:
            # Custom search across both tables
            query = query.where(or_(
                col(User.email).ilike(f"%{search_query}%"),
                col(Customer.first_name).ilike(f"%{search_query}%"),
                col(Customer.last_name).ilike(f"%{search_query}%"),
                col(Customer.phone_number).ilike(f"%{search_query}%")
            ))

        # Sort
        # Try to sort on User first, then Customer
        if hasattr(User, sort_by):
             query = apply_sorting(query, User, sort_by, SortOrder(sort_order))
        elif hasattr(Customer, sort_by):
             query = apply_sorting(query, Customer, sort_by, SortOrder(sort_order))
        else:
             query = query.order_by(User.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        
        total = (await self.session.execute(count_query)).scalar_one()
        result = await self.session.execute(query.offset(skip).limit(limit))
        rows = result.all()
        
        customers = []
        for customer, user in rows:
            customers.append(CustomerDetailResponse(
                id=customer.id,
                user_id=user.id,
                email=user.email,
                first_name=customer.first_name,
                last_name=customer.last_name,
                phone_number=customer.phone_number,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at
            ))
            
        return customers, total

    async def get_customer(self, customer_id: UUID) -> CustomerDetailResponse:
        """Get customer by ID."""
        query = select(Customer, User).join(User).where(
            (Customer.id == customer_id) & (User.deleted_at == None)
        )
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="Customer not found")
            
        customer, user = row
        return CustomerDetailResponse(
            id=customer.id,
            user_id=user.id,
            email=user.email,
            first_name=customer.first_name,
            last_name=customer.last_name,
            phone_number=customer.phone_number,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def update_customer(self, customer_id: UUID, data: CustomerUpdate, actor_id: UUID, request: Optional[Request] = None) -> CustomerDetailResponse:
        """Update customer."""
        customer = await self.customer_repo.get(customer_id)
        if not customer:
             raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="Customer not found")
        user = await self.user_repo.get(customer.user_id)

        old_values = {
            "email": user.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone": customer.phone_number
        }

        user_updates = {}
        if data.email and data.email != user.email:
            existing = await self.user_repo.get_by_email(data.email)
            if existing and existing.id != user.id:
                 raise ConflictError(error_code=ErrorCode.USER_ALREADY_EXISTS, message="Email already in use")
            user_updates["email"] = data.email
        
        if data.password:
            user_updates["hashed_password"] = get_password_hash(data.password)

        if data.is_active is not None:
             user_updates["is_active"] = data.is_active

        if user_updates:
            await self.user_repo.update(user, user_updates)

        customer_updates = {}
        if data.first_name: customer_updates["first_name"] = data.first_name
        if data.last_name: customer_updates["last_name"] = data.last_name
        if data.phone_number: customer_updates["phone_number"] = data.phone_number
        
        if customer_updates:
            await self.customer_repo.update(customer, customer_updates)
            
        # Invalidate Cache
        from app.core.cache import delete_cache, user_profile_key
        await delete_cache(user_profile_key(str(user.id)))

        # Audit
        new_values = {
            "email": user.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone": customer.phone_number
        }
        await audit_service.log_action(
            action="update_customer",
            actor_id=actor_id,
            target_id=str(customer.id),
            target_type="customer",
            old_values=old_values,
            new_values=new_values,
            request=request
        )

        return await self.get_customer(customer_id)

    async def delete_customer(self, customer_id: UUID, actor_id: UUID, request: Optional[Request] = None):
        """Soft delete customer."""
        customer = await self.customer_repo.get(customer_id)
        if not customer:
             raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="Customer not found")
             
        success = await self.user_repo.soft_delete(customer.user_id)
        if not success:
             raise NotFoundError(error_code=ErrorCode.USER_NOT_FOUND, message="User not found")
             
        # Invalidate Cache
        from app.core.cache import delete_cache, user_profile_key
        await delete_cache(user_profile_key(str(customer.user_id)))
             
        await audit_service.log_action(
            action="delete_customer",
            actor_id=actor_id,
            target_id=str(customer.id),
            target_type="customer",
            details={"user_id": str(customer.user_id)},
            request=request
        )
