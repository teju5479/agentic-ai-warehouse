from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.inventory import Inventory
from app.schemas.inventory_schemas import InventorySchema

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

@router.get("", response_model=list[InventorySchema])
def list_inventory(db: Session = Depends(get_db)):
    items = db.query(Inventory).all()
    return [InventorySchema.model_validate(i) for i in items]

@router.get("/{sku}", response_model=InventorySchema)
def get_inventory(sku: str, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.sku == sku).first()
    if not item:
        raise HTTPException(404, f"Inventory for SKU {sku} not found")
    return InventorySchema.model_validate(item)
