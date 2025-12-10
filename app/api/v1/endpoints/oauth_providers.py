"""
OAuth Provider management endpoints for admin.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.docs import doc_responses
from app.core.permissions import require_permissions
from app.schemas.response import SuccessResponse
from app.schemas.oauth_provider import (
    OAuthProviderCreateRequest,
    OAuthProviderUpdateRequest,
    OAuthProviderStatusRequest
)
from app.constants import PermissionEnum
from app.services.oauth_provider_service import OAuthProviderService

router = APIRouter(tags=["OAuth Provider Management"])


@router.post(
    "",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create OAuth Provider",
    responses=doc_responses(
        success_example={"id": "550e8400-e29b-41d4-a716-446655440000", "name": "google"},
        success_message="OAuth provider created successfully",
        errors=(401, 403, 409, 422)
    )
)
async def create_oauth_provider(
    request: OAuthProviderCreateRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.OAUTH_PROVIDERS_WRITE]))
):
    """
    Create a new OAuth provider.
    
    - Requires `oauth_providers:write` permission
    - Provider name must be unique
    """
    service = OAuthProviderService(db)
    provider_data = await service.create_provider(
        name=request.name,
        display_name=request.display_name,
        client_id=request.client_id,
        client_secret=request.client_secret,
        authorization_url=request.authorization_url,
        token_url=request.token_url,
        user_info_url=request.user_info_url,
        scopes=request.scopes,
        icon=request.icon,
        is_active=request.is_active,
        actor_id=current_user.id,
        request=req
    )
    
    return SuccessResponse(
        message="OAuth provider created successfully",
        data=provider_data
    )


@router.get(
    "",
    response_model=SuccessResponse,
    summary="List OAuth Providers",
    responses=doc_responses(
        success_example={"items": [{"id": "...", "name": "google"}], "total": 1, "page": 1},
        success_message="OAuth providers retrieved successfully",
        errors=(401, 403)
    )
)
async def list_oauth_providers(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.OAUTH_PROVIDERS_READ]))
):
    """
    List all OAuth providers (active and inactive) with pagination.
    
    - Requires `oauth_providers:read` permission
    - Returns paginated results with metadata
    """
    service = OAuthProviderService(db)
    result = await service.list_providers(
        include_inactive=True,
        page=page,
        per_page=per_page
    )
    
    return SuccessResponse(
        message="OAuth providers retrieved successfully",
        data=result
    )


@router.get(
    "/{provider_id}",
    response_model=SuccessResponse,
    summary="Get OAuth Provider Details",
    responses=doc_responses(
        success_example={"id": "...", "name": "google", "client_id": "...", "scopes": ["email", "profile"]},
        success_message="OAuth provider retrieved successfully",
        errors=(401, 403, 404)
    )
)
async def get_oauth_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.OAUTH_PROVIDERS_READ]))
):
    """
    Get OAuth provider details.
    
    - Requires `oauth_providers:read` permission
    - Returns full configuration (except client_secret)
    """
    service = OAuthProviderService(db)
    provider_data = await service.get_provider(provider_id)
    
    return SuccessResponse(
        message="OAuth provider retrieved successfully",
        data=provider_data
    )


@router.put(
    "/{provider_id}",
    response_model=SuccessResponse,
    summary="Update OAuth Provider",
    responses=doc_responses(
        success_example=None,
        success_message="OAuth provider updated successfully",
        errors=(401, 403, 404, 422)
    )
)
async def update_oauth_provider(
    provider_id: UUID,
    request: OAuthProviderUpdateRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.OAUTH_PROVIDERS_WRITE]))
):
    """
    Update OAuth provider configuration.
    
    - Requires `oauth_providers:write` permission
    """
    service = OAuthProviderService(db)
    update_data = request.model_dump(exclude_unset=True)
    await service.update_provider(
        provider_id, 
        actor_id=current_user.id, 
        request=req,
        **update_data
    )
    
    return SuccessResponse(
        message="OAuth provider updated successfully",
        data=None
    )


@router.patch(
    "/{provider_id}/status",
    response_model=SuccessResponse,
    summary="Activate/Deactivate OAuth Provider",
    responses=doc_responses(
        success_example={"is_active": True},
        success_message="OAuth provider status updated successfully",
        errors=(401, 403, 404)
    )
)
async def update_oauth_provider_status(
    provider_id: UUID,
    request: OAuthProviderStatusRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.OAUTH_PROVIDERS_WRITE]))
):
    """
    Activate or deactivate an OAuth provider.
    
    - Requires `oauth_providers:write` permission
    - Set `is_active` to true to activate, false to deactivate
    - Deactivated providers won't appear in public provider list
    """
    service = OAuthProviderService(db)
    status_data = await service.update_status(
        provider_id, 
        request.is_active, 
        actor_id=current_user.id, 
        request=req
    )
    
    status_text = "activated" if request.is_active else "deactivated"
    
    return SuccessResponse(
        message=f"OAuth provider {status_text} successfully",
        data=status_data
    )


@router.delete(
    "/{provider_id}",
    response_model=SuccessResponse,
    summary="Delete OAuth Provider",
    responses=doc_responses(
        success_example=None,
        success_message="OAuth provider deleted successfully",
        errors=(401, 403, 404)
    )
)
async def delete_oauth_provider(
    provider_id: UUID,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permissions([PermissionEnum.OAUTH_PROVIDERS_DELETE]))
):
    """
    Delete an OAuth provider.
    
    - Requires `oauth_providers:delete` permission
    - Will fail if provider has linked accounts
    """
    service = OAuthProviderService(db)
    await service.delete_provider(
        provider_id, 
        actor_id=current_user.id, 
        request=req
    )
    
    return SuccessResponse(
        message="OAuth provider deleted successfully",
        data=None
    )
