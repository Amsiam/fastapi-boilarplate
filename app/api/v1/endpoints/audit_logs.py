"""
Audit Log Viewer Endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.permissions import get_current_active_user
from app.core.docs import doc_responses
from app.models.user import User
from app.services.audit_service import audit_service
from app.schemas.response import SuccessResponse
from app.constants.enums import UserRole
from app.schemas.response import ErrorCode
from app.core.exceptions import PermissionDeniedError

router = APIRouter(tags=["Audit Logs"])

@router.get(
    "/",
    response_model=SuccessResponse,
    summary="List Audit Logs",
    responses=doc_responses(
        success_example={
            "items": [{"action": "create_role", "actor_id": "...", "timestamp": "2024-01-01T00:00:00"}],
            "total": 100,
            "page": 1,
            "per_page": 20
        },
        success_message="Audit logs retrieved successfully",
        errors=(401, 403)
    )
)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    List audit logs. Only accessible by Admins.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedError(
            error_code=ErrorCode.PERMISSION_DENIED,
            message="Only admins can view audit logs"
        )
        
    skip = (page - 1) * per_page
    logs, total = await audit_service.list_logs(
        skip=skip,
        limit=per_page,
        action=action,
        target_type=target_type,
        actor_id=actor_id
    )
    
    return SuccessResponse(
        message="Audit logs retrieved successfully",
        data={
            "items": logs,
            "total": total,
            "page": page,
            "per_page": per_page
        }
    )
