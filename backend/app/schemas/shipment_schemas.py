from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ShipmentSchema(BaseModel):
    shipment_id: str
    order_id: str
    status: str
    carrier: str
    tracking_reference: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    destination: str
    
    model_config = {"from_attributes": True}
