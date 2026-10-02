"""Shipment management tools for agent workflows."""
from sqlalchemy.orm import Session
from app.models.shipment import Shipment
from app.models.order import Order
from app.services.audit_service import create_audit_entry
from app.core.validation import validate_order_id


def get_shipment(db: Session, order_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Get shipment(s) for an order."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    if not shipments:
        return {"success": False, "error": f"No shipments found for order {order_id}"}
    
    result = {
        "success": True,
        "shipments": [
            {
                "shipment_id": s.shipment_id,
                "order_id": s.order_id,
                "status": s.status,
                "carrier": s.carrier,
                "tracking_reference": s.tracking_reference,
                "destination": s.destination,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in shipments
        ]
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_shipment", {"order_id": order_id}, result=result, outcome="SUCCESS")
    
    return result


def get_all_shipments(db: Session, run_id: str = "", workflow: str = "") -> dict:
    """List all shipments."""
    shipments = db.query(Shipment).all()
    
    result = {
        "success": True,
        "shipments": [
            {
                "shipment_id": s.shipment_id,
                "order_id": s.order_id,
                "status": s.status,
                "carrier": s.carrier,
                "tracking_reference": s.tracking_reference,
                "destination": s.destination,
            }
            for s in shipments
        ],
        "count": len(shipments)
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_all_shipments", {}, result={"count": len(shipments)}, outcome="SUCCESS")
    
    return result


def check_shipment_order_consistency(db: Session, order_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Compare order vs shipment status and destination, flag conflicts."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return {"success": False, "error": f"Order {order_id} not found"}
    
    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    if not shipments:
        return {"success": False, "error": f"No shipments found for order {order_id}"}
    
    conflicts = []
    
    for s in shipments:
        # Check status consistency
        if order.status == "PROCESSING" and s.status == "DELIVERED":
            conflicts.append(f"Status conflict: Order {order_id} is PROCESSING but shipment {s.shipment_id} shows DELIVERED")
        elif order.status == "PENDING" and s.status in ["DELIVERED", "IN_TRANSIT"]:
            conflicts.append(f"Status conflict: Order {order_id} is PENDING but shipment {s.shipment_id} shows {s.status}")
        elif order.status == "COMPLETED" and s.status == "PENDING":
            conflicts.append(f"Status conflict: Order {order_id} is COMPLETED but shipment {s.shipment_id} is still PENDING")
        
        # Check destination consistency
        if order.destination != s.destination:
            conflicts.append(f"Destination conflict: Order destination={order.destination}, Shipment {s.shipment_id} destination={s.destination}")
    
    result = {
        "success": True,
        "order_id": order_id,
        "order_status": order.status,
        "order_destination": order.destination,
        "is_consistent": len(conflicts) == 0,
        "conflicts": conflicts,
        "shipments": [
            {"shipment_id": s.shipment_id, "status": s.status, "destination": s.destination}
            for s in shipments
        ]
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "check_shipment_order_consistency", 
                          {"order_id": order_id}, result=result, outcome="SUCCESS")
    
    return result
