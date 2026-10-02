"""Order management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.order import Order, OrderLine
from app.schemas.order_schemas import OrderSchema, OrderDetailSchema, OrderLineSchema

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("", response_model=list[OrderSchema])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return [OrderSchema.model_validate(o) for o in orders]


@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(404, f"Order {order_id} not found")
    lines = db.query(OrderLine).filter(OrderLine.order_id == order_id).all()
    return {
        **OrderSchema.model_validate(order).model_dump(),
        "order_lines": [OrderLineSchema.model_validate(l).model_dump() for l in lines]
    }
