"""
OAuth2 provider model for social authentication.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


class OAuthProvider(SQLModel, table=True):
    """OAuth2 provider configuration."""
    __tablename__ = "oauth_providers"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=50)  # e.g., "google", "github"
    display_name: str = Field(max_length=100)  # e.g., "Google", "GitHub"
    icon: Optional[str] = Field(default=None, max_length=255)  # URL or icon identifier
    client_id: str = Field(max_length=255)
    client_secret: str = Field(max_length=255)  # Encrypted in production
    authorization_url: str = Field(max_length=500)
    token_url: str = Field(max_length=500)
    user_info_url: str = Field(max_length=500)
    scopes: list[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OAuthAccount(SQLModel, table=True):
    """Links users to their OAuth provider accounts."""
    __tablename__ = "oauth_accounts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    provider_id: UUID = Field(foreign_key="oauth_providers.id", index=True)
    provider_user_id: str = Field(max_length=255, index=True)  # User ID from provider
    email: str = Field(max_length=255)  # Email from provider
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Unique constraint: one provider account per user per provider
    __table_args__ = (
        {"schema": None},
    )
