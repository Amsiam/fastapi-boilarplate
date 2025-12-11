"""
User models for authentication and authorization.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel

from app.constants.enums import UserType


class User(SQLModel, table=True):
    """Base user model."""
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    user_type: UserType = Field(sa_column_kwargs={"nullable": False})
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: Optional["Customer"] = Relationship(back_populates="user")
    admin: Optional["Admin"] = Relationship(back_populates="user")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")


class Customer(SQLModel, table=True):
    """Customer-specific user data."""
    __tablename__ = "customers"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", unique=True, index=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)

    # Relationships
    user: User = Relationship(back_populates="customer")


class Admin(SQLModel, table=True):
    """Admin-specific user data with RBAC."""
    __tablename__ = "admins"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", unique=True, index=True)
    username: str = Field(unique=True, index=True, max_length=100)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    is_super_admin: bool = Field(default=False)  # Super admin cannot be edited/deleted
    permission_overrides: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    # Relationships
    user: User = Relationship(back_populates="admin")
    role: "Role" = Relationship(back_populates="admins")


# Import to avoid circular dependency
from app.modules.roles.models import Role  # noqa: E402
from app.modules.auth.token_models import RefreshToken  # noqa: E402
