"""
Audit Log model for MongoDB.
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class AuditLog(BaseModel):
    """Audit log entry for MongoDB."""
    action: str
    actor_id: str  # Admin ID (UUID as string)
    target_id: Optional[str] = None
    target_type: Optional[str] = None  # e.g., "user", "role"
    details: Optional[Dict[str, Any]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
