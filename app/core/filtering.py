from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from enum import Enum
from pydantic import BaseModel
from sqlmodel import SQLModel, select, col, or_, desc, asc
from sqlalchemy.sql.expression import Select

ModelType = TypeVar("ModelType", bound=SQLModel)

class FilterOperator(str, Enum):
    EQ = "eq"          # =
    GT = "gt"          # >
    LT = "lt"          # <
    GTE = "gte"        # >=
    LTE = "lte"        # <=
    NE = "ne"          # !=
    LIKE = "like"      # LIKE %value% (case sensitive)
    ILIKE = "ilike"    # ILIKE %value% (case insensitive)
    IN = "in"          # IN (list)

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

def apply_filters(
    query: Select, 
    model: Type[ModelType], 
    filters: Dict[str, Any]
) -> Select:
    """
    Apply dictionary-based filters to a query.
    Rules:
    - simple_key=value -> equals
    - key__op=value -> applies operator
    """
    for key, value in filters.items():
        if value is None:
            continue
            
        # Parse field and operator
        if "__" in key:
            field_name, op = key.split("__", 1)
        else:
            field_name, op = key, "eq"
            
        # Check if field exists on model
        if not hasattr(model, field_name):
            continue
            
        field = getattr(model, field_name)
        
        # Apply operator
        try:
            operator = FilterOperator(op)
        except ValueError:
            continue  # Invalid operator
        
        if operator == FilterOperator.EQ:
            query = query.where(field == value)
        elif operator == FilterOperator.NE:
            query = query.where(field != value)
        elif operator == FilterOperator.GT:
            query = query.where(field > value)
        elif operator == FilterOperator.GTE:
            query = query.where(field >= value)
        elif operator == FilterOperator.LT:
            query = query.where(field < value)
        elif operator == FilterOperator.LTE:
            query = query.where(field <= value)
        elif operator == FilterOperator.LIKE:
            query = query.where(col(field).like(f"%{value}%"))
        elif operator == FilterOperator.ILIKE:
            query = query.where(col(field).ilike(f"%{value}%"))
        elif operator == FilterOperator.IN:
            if isinstance(value, (list, tuple)):
                query = query.where(col(field).in_(value))
            elif isinstance(value, str):
                query = query.where(col(field).in_(value.split(",")))

    return query

def apply_sorting(
    query: Select, 
    model: Type[ModelType], 
    sort_by: str = "created_at", 
    sort_order: SortOrder = SortOrder.DESC
) -> Select:
    """
    Apply sorting to a query.
    """
    if not hasattr(model, sort_by):
        # Default fallback
        if hasattr(model, "created_at"):
            return query.order_by(desc(getattr(model, "created_at")))
        return query

    field = getattr(model, sort_by)
    if sort_order == SortOrder.DESC:
        return query.order_by(desc(field))
    else:
        return query.order_by(asc(field))

def apply_search(
    query: Select,
    model: Type[ModelType],
    search_query: str,
    search_fields: List[str]
) -> Select:
    """
    Apply global search across multiple fields (OR condition).
    """
    if not search_query or not search_fields:
        return query
        
    expressions = []
    for field_name in search_fields:
        if hasattr(model, field_name):
            field = getattr(model, field_name)
            # Use ILIKE for search
            expressions.append(col(field).ilike(f"%{search_query}%"))
            
    if expressions:
        query = query.where(or_(*expressions))
        
    return query
