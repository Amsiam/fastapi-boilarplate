"""
Role and Permission models for RBAC.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class Role(SQLModel, table=True):
    """Role model for RBAC."""
    __tablename__ = "roles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_system: bool = Field(default=False)  # True for default roles
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    admins: list["Admin"] = Relationship(back_populates="role")
    role_permissions: list["RolePermission"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Permission(SQLModel, table=True):
    """Permission model for RBAC."""
    __tablename__ = "permissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(unique=True, index=True)  # e.g., "users:read"
    description: str
    resource: Optional[str] = Field(default=None, max_length=50)  # e.g., "users" (optional, can be derived from code)
    action: Optional[str] = Field(default=None, max_length=50)    # e.g., "read" (optional, can be derived from code)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    role_permissions: list["RolePermission"] = Relationship(back_populates="permission")


class RolePermission(SQLModel, table=True):
    """Association table for Role-Permission many-to-many relationship."""
    __tablename__ = "role_permissions"

    role_id: UUID = Field(foreign_key="roles.id", primary_key=True)
    permission_id: UUID = Field(foreign_key="permissions.id", primary_key=True)

    # Relationships
    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")


# Import to avoid circular dependency
from app.modules.users.models import Admin  # noqa: E402
