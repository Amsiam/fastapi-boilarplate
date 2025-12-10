"""
OAuth2 endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.schemas.response import SuccessResponse
from app.schemas.auth import OAuthCallbackRequest, Token
from app.services.oauth_service import OAuthService

router = APIRouter(tags=["OAuth"])


@router.get(
    "/providers",
    response_model=SuccessResponse,
    summary="List OAuth Providers"
)
async def list_providers(
    db: AsyncSession = Depends(get_db)
):
    """
    List available OAuth providers.
    
    Returns:
        List of providers with login URLs
    """
    service = OAuthService(db)
    providers = await service.list_providers()
    
    return SuccessResponse(
        message="Providers retrieved successfully",
        data=providers
    )


@router.get(
    "/login/{provider}",
    response_model=SuccessResponse,
    summary="Get OAuth Login URL"
)
async def get_login_url(
    provider: str,
    redirect_uri: str = Query(..., description="Callback URL"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get authorization URL for a provider.
    
    Args:
        provider: Provider name (e.g., google)
        redirect_uri: URL where provider should redirect back
        
    Returns:
        Authorization URL
    """
    service = OAuthService(db)
    url = await service.get_login_url(provider, redirect_uri)
    
    return SuccessResponse(
        message="Login URL generated successfully",
        data={"url": url}
    )


@router.post(
    "/callback",
    response_model=SuccessResponse,
    summary="OAuth Callback"
)
async def oauth_callback(
    request: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback and exchange code for tokens.
    
    Args:
        request: Callback data (provider, code, redirect_uri)
        
    Returns:
        Access and refresh tokens
    """
    service = OAuthService(db)
    tokens = await service.handle_callback(
        provider_name=request.provider,
        code=request.code,
        redirect_uri=request.redirect_uri
    )
    
    return SuccessResponse(
        message="Login successful",
        data=tokens
    )
