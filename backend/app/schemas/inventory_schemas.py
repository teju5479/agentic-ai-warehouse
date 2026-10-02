from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InventorySchema(BaseModel):
    sku: str
    location_id: str
    on_hand: int
    reserved: int
    available: int
    last_updated: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class InventoryReadinessSchema(BaseModel):
    sku: str
    requested: int
    remaining_needed: int
    available: int
    sufficient: bool
    shortfall: int = 0
    note: str = ""
