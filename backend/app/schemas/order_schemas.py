"""Pydantic schemas for Order API."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class OrderLineSchema(BaseModel):
    sku: str
    requested_qty: int
    picked_qty: int = 0
    status: str = "PENDING"
    
    model_config = {"from_attributes": True}


class OrderSchema(BaseModel):
    order_id: str
    status: str
    created_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    priority: str
    destination: str
    held_reason: Optional[str] = None
    
    model_config = {"from_attributes": True}


class OrderDetailSchema(OrderSchema):
    order_lines: list[OrderLineSchema] = []


class OrderStatusUpdateRequest(BaseModel):
    status: str
    reason: str = ""


class OrderHoldRequest(BaseModel):
    reason: str
