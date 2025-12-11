"""
Audit Log Viewer Endpoints.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status, Request
from app.core.permissions import get_current_active_user
from app.core.docs import doc_responses
from app.modules.users.models import User
from app.modules.audit.service import audit_service
from app.core.schemas.response import SuccessResponse, PaginatedResponse
from app.constants.enums import UserType
from app.core.schemas.response import ErrorCode
from app.core.exceptions import PermissionDeniedError

router = APIRouter(tags=["Audit Logs"])

@router.get(
    "/",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="List Audit Logs",
    responses=doc_responses(
        success_message="Audit logs retrieved successfully",
        errors=(401, 403)
    )
)
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Search query"),
    sort: str = Query("timestamp", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    # Explicit filters for documentation
    action: Optional[str] = Query(None, description="Filter by action"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    current_user: User = Depends(get_current_active_user)
):
    """
    List audit logs. Only accessible by Admins.
    Supports filtering (e.g. ?action=create_user), searching (?q=...), and sorting.
    """
    if current_user.user_type != UserType.ADMIN:
        raise PermissionDeniedError(
            error_code=ErrorCode.PERMISSION_DENIED,
            message="Only admins can view audit logs"
        )

    # Construct filters from query params
    # We include explicitly defined ones and potentially others if we wanted dynamic
    filters = {}
    if action: filters["action"] = action
    if target_type: filters["target_type"] = target_type
    if actor_id: filters["actor_id"] = actor_id
    
    # Capture other typical filters like timestamps if passed manually in query string
    # e.g. timestamp__gt
    for key, value in request.query_params.items():
        if "__" in key:
            filters[key] = value
        
    skip = (page - 1) * per_page
    logs, total = await audit_service.list_logs(
        skip=skip,
        limit=per_page,
        filters=filters,
        search_query=q,
        sort_by=sort,
        sort_order=order
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
