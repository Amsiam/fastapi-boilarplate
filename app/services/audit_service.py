"""
Audit Service for logging actions to MongoDB.
"""
from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import Request

from app.core.mongo import mongodb
from app.models.audit import AuditLog

class AuditService:
    """Service for handling audit logs."""
    
    async def log_action(
        self,
        action: str,
        actor_id: UUID,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> None:
        """
        Record an audit log entry.
        
        Args:
            action: Description of the action (e.g., "delete_user")
            actor_id: ID of the user performing the action
            target_id: ID of the entity being affected
            target_type: Type of the entity (e.g., "user", "role")
            details: Additional context
            old_values: State before change
            new_values: State after change
            request: FastAPI request object (for IP/User-Agent extraction)
        """
        db = mongodb.get_db()
        collection = db["audit_logs"]
        
        ip_address = None
        user_agent = None
        
        if request:
            if request.client:
                ip_address = request.client.host
            user_agent = request.headers.get("user-agent")

        log_entry = AuditLog(
            action=action,
            actor_id=str(actor_id),
            target_id=str(target_id) if target_id else None,
            target_type=target_type,
            details=details,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        try:
            data = log_entry.model_dump()
        except AttributeError:
            data = log_entry.dict()
            
        await collection.insert_one(data)

# Global instance
audit_service = AuditService()
