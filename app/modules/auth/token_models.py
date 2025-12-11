"""
Authentication-related models (RefreshToken).
OTP is handled via Redis, no SQL model needed.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class RefreshToken(SQLModel, table=True):
    """Refresh token model for JWT rotation."""
    __tablename__ = "refresh_tokens"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(unique=True, index=True, max_length=255)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = Field(default=False)
    family_id: UUID = Field(default_factory=uuid4, index=True)  # For rotation tracking
    parent_token_id: Optional[UUID] = Field(default=None)  # For chain tracking

    # Relationships
    user: "User" = Relationship(back_populates="refresh_tokens")


# Import to avoid circular dependency
from app.modules.users.models import User  # noqa: E402
