from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.order import Order
from app.models.exception import ExceptionRecord
from app.models.picker import Picker
from app.models.plan import Plan

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status.in_(["PENDING", "PROCESSING"])).count()
    blocked_orders = db.query(Order).filter(Order.status == "BLOCKED").count()
    held_orders = db.query(Order).filter(Order.status == "HELD").count()
    completed_orders = db.query(Order).filter(Order.status == "COMPLETED").count()
    open_exceptions = db.query(ExceptionRecord).filter(ExceptionRecord.status.in_(["OPEN", "INVESTIGATING", "WAITING_FOR_APPROVAL"])).count()
    available_pickers = db.query(Picker).filter(Picker.availability == "AVAILABLE").count()
    total_pickers = db.query(Picker).count()
    latest_plan = db.query(Plan).order_by(Plan.created_at.desc()).first()
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "blocked_orders": blocked_orders,
        "held_orders": held_orders,
        "completed_orders": completed_orders,
        "open_exceptions": open_exceptions,
        "available_pickers": available_pickers,
        "total_pickers": total_pickers,
        "current_plan": {
            "plan_id": latest_plan.plan_id if latest_plan else None,
            "version": latest_plan.version if latest_plan else None,
            "status": latest_plan.status if latest_plan else None
        } if latest_plan else None
    }
