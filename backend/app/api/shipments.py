from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.shipment import Shipment
from app.schemas.shipment_schemas import ShipmentSchema

router = APIRouter(prefix="/api/shipments", tags=["Shipments"])

@router.get("", response_model=list[ShipmentSchema])
def list_shipments(db: Session = Depends(get_db)):
    shipments = db.query(Shipment).all()
    return [ShipmentSchema.model_validate(s) for s in shipments]

@router.get("/{order_id}", response_model=list[ShipmentSchema])
def get_shipments_for_order(order_id: str, db: Session = Depends(get_db)):
    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    return [ShipmentSchema.model_validate(s) for s in shipments]
