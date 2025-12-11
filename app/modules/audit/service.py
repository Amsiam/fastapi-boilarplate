"""
Audit Service for logging actions to MongoDB.
"""
from typing import Any, Dict, Optional, List
from uuid import UUID
from fastapi import Request

from app.core.mongo import mongodb
from app.modules.audit.models import AuditLog

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


    
    def _build_mongo_query(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert standard filters (field__op=value) to MongoDB query.
        """
        query = {}
        
        for key, value in filters.items():
            if "__" in key:
                field, op = key.split("__", 1)
            else:
                field, op = key, "eq"
                
            if field == "id":
                field = "_id"
                
            if op == "eq":
                query[field] = value
            elif op == "ne":
                query[field] = {"$ne": value}
            elif op == "gt":
                query[field] = {"$gt": value}
            elif op == "gte":
                query[field] = {"$gte": value}
            elif op == "lt":
                query[field] = {"$lt": value}
            elif op == "lte":
                query[field] = {"$lte": value}
            elif op == "in":
                # Expecting list or comma-separated string if coming from query params
                if isinstance(value, str):
                    value = value.split(",")
                query[field] = {"$in": value}
            elif op in ("like", "ilike", "contains"):
                # MongoDB regex is case-sensitive by default. $options: 'i' for case-insensitive
                query[field] = {"$regex": value, "$options": "i"}
                
        return query

    async def list_logs(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List audit logs with filtering, searching, and pagination.
        """
        db = mongodb.get_db()
        collection = db["audit_logs"]
        
        # 1. Build Query
        query = {}
        if filters:
            mongo_filters = self._build_mongo_query(filters)
            query.update(mongo_filters)
            
        # 2. Apply Search
        if search_query:
            # Search logic: specific fields or text index
            # Using regex for simplicity on commonly searched fields
            search_regex = {"$regex": search_query, "$options": "i"}
            query["$or"] = [
                {"action": search_regex},
                {"target_type": search_regex},
                {"actor_id": search_regex},
                {"details.email": search_regex}, # Common detail
                {"details.username": search_regex}
            ]

        # 3. Get Total
        total = await collection.count_documents(query)
        
        # 4. Sorting
        mongo_sort_order = -1 if sort_order.lower() == "desc" else 1
        
        # 5. Execute
        cursor = collection.find(query).sort(sort_by, mongo_sort_order).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for log in logs:
            if "_id" in log:
                log["_id"] = str(log["_id"])
                
        return logs, total

# Global instance
audit_service = AuditService()
