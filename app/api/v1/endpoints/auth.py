"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, Response, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.docs import doc_responses
from app.core.permissions import get_current_verified_user, get_current_user
from app.schemas.auth import (
    UserRegisterRequest,
    LoginRequest,
    EmailVerificationRequest,
    ResendOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse
)
from app.schemas.response import SuccessResponse
from app.services import AuthService, OTPService
from app.constants.enums import OTPType

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Customer",
    responses=doc_responses(
        success_example=None,
        success_message="User registered successfully. Please verify your email.",
        errors=(409, 422)
    )
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new customer user.
    
    - Creates inactive account requiring email verification
    - Sends OTP to provided email
    - Returns success message
    """
    auth_service = AuthService(db)
    
    # Register user
    user = await auth_service.register_customer(
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        phone_number=request.phone_number
    )
    
    # Generate OTP for email verification
    otp_code = await OTPService.generate_otp(user.email, OTPType.EMAIL_VERIFICATION)
    
    # TODO: Send email with OTP
    # await send_verification_email(user.email, otp_code)
    print(f"[DEV] OTP for {user.email}: {otp_code}")  # Remove in production
    
    return SuccessResponse(
        message="User registered successfully. Please verify your email.",
        data=None
    )


@router.post(
    "/login",
    response_model=SuccessResponse,
    summary="Login",
    responses=doc_responses(
        success_example={
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        },
        success_message="Login successful",
        errors=(401, 403, 422)
    )
)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    - Authenticates user credentials
    - Returns access token (15min expiry) in response body
    - Sets refresh token in HttpOnly cookie (7 days expiry)
    - Customers must have verified email
    
    **Note:** Refresh token is automatically set in HttpOnly cookie.
    Use `/auth/refresh` endpoint to get a new access token.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = await auth_service.authenticate_user(request.username, request.password)
    
    # Check email verification for customers
    from app.constants.enums import UserRole
    from app.core.exceptions import AuthenticationError
    from app.schemas.response import ErrorCode
    
    if user.role == UserRole.CUSTOMER and not user.is_verified:
        raise AuthenticationError(
            error_code=ErrorCode.EMAIL_NOT_VERIFIED,
            message="Please verify your email before logging in"
        )
    
    # Create tokens
    access_token, refresh_token = await auth_service.create_tokens(user)
    
    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return SuccessResponse(
        message="Login successful",
        data={
            "access_token": access_token,
            "token_type": "bearer"
        }
    )


@router.post(
    "/verify-email",
    response_model=SuccessResponse,
    summary="Verify Email",
    responses=doc_responses(
        success_example=None,
        success_message="Email verified successfully. You can now login.",
        errors=(400, 422)
    )
)
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email with OTP code.
    
    - Validates OTP code (6 digits, max 3 attempts)
    - Activates user account
    - Allows user to login
    """
    auth_service = AuthService(db)
    
    # Verify OTP
    await OTPService.verify_otp(request.email, request.otp, OTPType.EMAIL_VERIFICATION)
    
    # Get user and mark as verified
    from app.repositories import UserRepository
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(request.email)
    
    if user:
        await auth_service.verify_email(str(user.id))
    
    return SuccessResponse(
        message="Email verified successfully. You can now login.",
        data=None
    )


@router.post(
    "/resend-otp",
    response_model=SuccessResponse,
    summary="Resend OTP",
    responses=doc_responses(
        success_example=None,
        success_message="OTP sent successfully",
        errors=(400, 422, 429)
    )
)
async def resend_otp(request: ResendOTPRequest):
    """
    Resend OTP code.
    
    - Respects 60-second cooldown between requests
    - Maximum 5 requests per hour (then 24-hour lockout)
    - Supports EMAIL_VERIFICATION and PASSWORD_RESET types
    """
    otp_type = OTPType(request.type)
    otp_code = await OTPService.generate_otp(request.email, otp_type)
    
    # TODO: Send email with OTP
    # await send_otp_email(request.email, otp_code, otp_type)
    print(f"[DEV] OTP for {request.email}: {otp_code}")  # Remove in production
    
    return SuccessResponse(message="OTP sent successfully", data=None)


@router.post(
    "/refresh",
    response_model=SuccessResponse,
    summary="Refresh Access Token",
    responses=doc_responses(
        success_example={
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        },
        success_message="Token refreshed successfully",
        errors=(401, 422)
    )
)
async def refresh_token(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token from cookie.
    
    - Reads refresh token from HttpOnly cookie
    - Validates refresh token
    - Implements token rotation (old token invalidated)
    - Detects token reuse and revokes entire token family
    - Returns new access token and sets new refresh token cookie
    
    **Note:** Refresh token is automatically read from HttpOnly cookie.
    """
    from fastapi import Request
    from app.core.exceptions import AuthenticationError
    from app.schemas.response import ErrorCode
    
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise AuthenticationError(
            error_code=ErrorCode.INVALID_REFRESH_TOKEN,
            message="Refresh token not provided"
        )
    
    auth_service = AuthService(db)
    
    # Refresh tokens
    new_access_token, new_refresh_token = await auth_service.refresh_access_token(refresh_token)
    
    # Set new refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return SuccessResponse(
        message="Token refreshed successfully",
        data={
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Logout",
    responses=doc_responses(
        success_example=None,
        success_message="Logged out successfully",
        errors=(401,)
    )
)
async def logout(
    response: Response,
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user.
    
    - Revokes all refresh tokens for the user
    - Blacklists current access token (immediate logout)
    - Clears refresh token cookie
    - Clears permission cache
    """
    from app.core.cache import set_cache
    from app.core.config import settings
    
    auth_service = AuthService(db)
    
    # Logout user (revoke refresh tokens)
    await auth_service.logout(str(current_user.id))
    
    # Blacklist current access token
    # Extract token from request
    token = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    
    if token:
        # Add to blacklist with TTL = remaining token lifetime (15 min)
        # Use hash of token to match the check in get_current_user
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        blacklist_key = f"blacklist:token:{token_hash}"
        await set_cache(blacklist_key, "1", expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")
    
    return SuccessResponse(message="Logged out successfully", data=None)


@router.get(
    "/me",
    response_model=SuccessResponse,
    summary="Get Current User",
    responses=doc_responses(
        success_example={
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "is_active": True,
            "is_verified": True,
            "role": "CUSTOMER",
            "created_at": "2024-01-01T00:00:00"
        },
        success_message="User retrieved successfully",
        errors=(401,)
    )
)
async def get_current_user_info(
    current_user = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information.
    
    - Requires valid access token
    - Requires verified email
    - Returns user profile data (including permissions for admins)
    """
    user_data = UserResponse.model_validate(current_user)
    
    # If user is admin, fetch role name and permissions
    from app.constants.enums import UserRole
    if current_user.role == UserRole.ADMIN:
        # Get permissions
        from app.core.permissions import get_user_permissions
        permissions = await get_user_permissions(current_user, db)
        user_data.permissions = permissions
        
        # Get role name
        from app.repositories import AdminRepository, RoleRepository
        admin_repo = AdminRepository(db)
        role_repo = RoleRepository(db)
        
        admin = await admin_repo.get_by_user_id(current_user.id)
        if admin:
            role = await role_repo.get(admin.role_id)
            if role:
                user_data.role_name = role.name
    
    return SuccessResponse(
        message="User retrieved successfully",
        data=user_data.model_dump(exclude_none=True)
    )
