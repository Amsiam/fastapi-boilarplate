"""
Authentication request and response schemas.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============= Request Schemas =============

class UserRegisterRequest(BaseModel):
    """Customer registration request."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)


class LoginRequest(BaseModel):
    """Login request (OAuth2 compatible)."""
    username: EmailStr  # OAuth2 uses 'username' field
    password: str


class EmailVerificationRequest(BaseModel):
    """Email verification request."""
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=100)


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class ResendOTPRequest(BaseModel):
    """Resend OTP request."""
    email: EmailStr
    type: str = Field(pattern="^(EMAIL_VERIFICATION|PASSWORD_RESET)$")


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""
    provider: str
    code: str
    redirect_uri: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# ============= Response Schemas =============

class Token(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenResponse(Token):
    """Token response (alias for backward compatibility)."""
    pass


class UserResponse(BaseModel):
    """Base user response."""
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    user_type: str
    role_name: Optional[str] = None
    permissions: Optional[list[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True




class CustomerResponse(BaseModel):
    """Customer response."""
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    first_name: str
    last_name: str
    phone_number: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminResponse(BaseModel):
    """Admin response."""
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    username: str
    role_name: str
    permissions: list[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OAuthLoginResponse(BaseModel):
    """OAuth login response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_new: bool


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class OAuthProviderResponse(BaseModel):
    """OAuth provider public response (no secrets)."""
    id: UUID
    name: str
    display_name: str
    icon: Optional[str]
    client_id: str
    authorization_url: str
    
    class Config:
        from_attributes = True


class OAuthProvidersResponse(BaseModel):
    """List of OAuth providers."""
    providers: list[OAuthProviderResponse]
