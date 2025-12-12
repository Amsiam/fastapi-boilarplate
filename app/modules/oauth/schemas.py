"""
OAuth Provider schemas.
"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============= Request Schemas =============

class OAuthProviderCreateRequest(BaseModel):
    """Create OAuth provider request."""
    name: str = Field(min_length=1, max_length=50, description="Unique provider name (e.g., 'google', 'github')")
    display_name: str = Field(min_length=1, max_length=100, description="Display name (e.g., 'Google', 'GitHub')")
    client_id: str = Field(min_length=1, max_length=255)
    client_secret: str = Field(min_length=1, max_length=255)
    authorization_url: str = Field(min_length=1, max_length=500)
    token_url: str = Field(min_length=1, max_length=500)
    user_info_url: str = Field(min_length=1, max_length=500)
    scopes: List[str] = Field(default_factory=list)
    icon: Optional[str] = Field(None, max_length=255)
    is_active: bool = Field(default=True)


class OAuthProviderUpdateRequest(BaseModel):
    """Update OAuth provider request."""
    display_name: Optional[str] = Field(None, max_length=100)
    client_id: Optional[str] = Field(None, max_length=255)
    client_secret: Optional[str] = Field(None, max_length=255)
    authorization_url: Optional[str] = Field(None, max_length=500)
    token_url: Optional[str] = Field(None, max_length=500)
    user_info_url: Optional[str] = Field(None, max_length=500)
    scopes: Optional[List[str]] = None
    icon: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class OAuthProviderStatusRequest(BaseModel):
    """Activate/deactivate OAuth provider request."""
    is_active: bool = Field(..., description="Set to true to activate, false to deactivate")


# ============= Response Schemas =============

class OAuthProviderResponse(BaseModel):
    """OAuth provider response."""
    id: UUID
    name: str
    display_name: str
    icon: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

    class Config:
        from_attributes = True


class OAuthProviderPublicResponse(BaseModel):
    """Public OAuth provider response."""
    name: str
    display_name: str
    icon: Optional[str]
    login_url: str


class OAuthProviderDetailResponse(BaseModel):
    """Detailed OAuth provider response."""
    id: UUID
    name: str
    display_name: str
    icon: Optional[str]
    client_id: str
    authorization_url: str
    token_url: str
    user_info_url: str
    scopes: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
