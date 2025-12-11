"""
User management schemas (Admin & Customer).
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

# ============= Admin Schemas =============

class AdminCreate(BaseModel):
    """Schema for creating a new admin."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    role_id: Optional[UUID] = None

class AdminUpdate(BaseModel):
    """Schema for updating an admin."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class AdminDetailResponse(BaseModel):
    """Detailed response for an Admin."""
    id: UUID  # Admin ID
    user_id: UUID
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Customer Schemas =============

class CustomerCreate(BaseModel):
    """Schema for creating a new customer."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: Optional[str] = None

class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class CustomerDetailResponse(BaseModel):
    """Detailed response for a Customer."""
    id: UUID  # Customer ID
    user_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
