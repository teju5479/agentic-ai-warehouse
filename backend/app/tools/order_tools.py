"""Order management tools for agent workflows."""
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.order import Order, OrderLine
from app.services.audit_service import create_audit_entry
from app.core.validation import validate_order_id, validate_status_transition
from app.core.rules import can_assign_order, requires_approval


def get_order(db: Session, order_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Retrieve order details by order_id."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return {"success": False, "error": f"Order {order_id} not found"}
    
    result = {
        "success": True,
        "order": {
            "order_id": order.order_id,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "deadline": order.deadline.isoformat() if order.deadline else None,
            "priority": order.priority,
            "destination": order.destination,
            "held_reason": order.held_reason
        }
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_order", {"order_id": order_id}, result=result["order"], outcome="SUCCESS")
    
    return result


def get_order_lines(db: Session, order_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Retrieve order lines for an order."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    lines = db.query(OrderLine).filter(OrderLine.order_id == order_id).all()
    if not lines:
        return {"success": False, "error": f"No order lines found for {order_id}"}
    
    result = {
        "success": True,
        "order_lines": [
            {
                "sku": l.sku,
                "requested_qty": l.requested_qty,
                "picked_qty": l.picked_qty,
                "status": l.status
            }
            for l in lines
        ]
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_order_lines", {"order_id": order_id}, result=result, outcome="SUCCESS")
    
    return result


def hold_order(db: Session, order_id: str, reason: str, run_id: str = "", workflow: str = "") -> dict:
    """Place an order on hold. Validates status transition."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        error = f"Order {order_id} not found"
        if run_id:
            create_audit_entry(db, run_id, workflow, "hold_order", {"order_id": order_id, "reason": reason}, error=error, outcome="FAILURE")
        return {"success": False, "error": error}
    
    transition = validate_status_transition(order.status, "HELD", "order")
    if not transition["valid"]:
        if run_id:
            create_audit_entry(db, run_id, workflow, "hold_order", {"order_id": order_id, "reason": reason}, error=transition["error"], outcome="FAILURE")
        return {"success": False, "error": transition["error"]}
    
    old_status = order.status
    order.status = "HELD"
    order.held_reason = reason
    db.commit()
    
    state_changes = {"order": order_id, "old_status": old_status, "new_status": "HELD", "reason": reason}
    if run_id:
        create_audit_entry(db, run_id, workflow, "hold_order", {"order_id": order_id, "reason": reason}, state_changes=state_changes, outcome="SUCCESS")
    
    return {"success": True, "order_id": order_id, "old_status": old_status, "new_status": "HELD", "reason": reason}


def update_order_status(db: Session, order_id: str, new_status: str, reason: str = "", run_id: str = "", workflow: str = "") -> dict:
    """Update order status with validation."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        error = f"Order {order_id} not found"
        if run_id:
            create_audit_entry(db, run_id, workflow, "update_order_status", {"order_id": order_id, "new_status": new_status}, error=error, outcome="FAILURE")
        return {"success": False, "error": error}
    
    # Check if action requires approval
    if new_status == "CANCELLED":
        approval_check = requires_approval("cancel_order")
        if approval_check["required"]:
            return {
                "success": False, 
                "error": "Action requires approval",
                "requires_approval": True,
                "policy": approval_check["policy"],
                "proposed_action": f"Change order {order_id} status to {new_status}"
            }
    
    transition = validate_status_transition(order.status, new_status, "order")
    if not transition["valid"]:
        if run_id:
            create_audit_entry(db, run_id, workflow, "update_order_status", {"order_id": order_id, "new_status": new_status}, error=transition["error"], outcome="FAILURE")
        return {"success": False, "error": transition["error"]}
    
    old_status = order.status
    order.status = new_status
    if reason:
        order.held_reason = reason
    db.commit()
    
    state_changes = {"order": order_id, "old_status": old_status, "new_status": new_status}
    if run_id:
        create_audit_entry(db, run_id, workflow, "update_order_status", {"order_id": order_id, "new_status": new_status, "reason": reason}, state_changes=state_changes, outcome="SUCCESS")
    
    return {"success": True, "order_id": order_id, "old_status": old_status, "new_status": new_status}


def find_duplicate_orders(db: Session, order_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Find potential duplicate orders by comparing destination and order lines."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return {"success": False, "error": f"Order {order_id} not found"}
    
    # Get order lines for the target order
    target_lines = db.query(OrderLine).filter(OrderLine.order_id == order_id).all()
    target_items = {(l.sku, l.requested_qty) for l in target_lines}
    
    # Find orders with same destination
    candidates = db.query(Order).filter(
        Order.destination == order.destination,
        Order.order_id != order_id,
        Order.status.notin_(["CANCELLED"])
    ).all()
    
    duplicates = []
    for candidate in candidates:
        cand_lines = db.query(OrderLine).filter(OrderLine.order_id == candidate.order_id).all()
        cand_items = {(l.sku, l.requested_qty) for l in cand_lines}
        
        # Check overlap
        overlap = target_items & cand_items
        if len(overlap) > 0 and len(overlap) >= len(target_items) * 0.5:
            similarity = len(overlap) / max(len(target_items), len(cand_items))
            duplicates.append({
                "order_id": candidate.order_id,
                "status": candidate.status,
                "destination": candidate.destination,
                "priority": candidate.priority,
                "similarity": round(similarity, 2),
                "matching_items": [(s, q) for s, q in overlap]
            })
    
    result = {
        "success": True,
        "source_order": order_id,
        "duplicates_found": len(duplicates),
        "duplicates": duplicates
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "find_duplicate_orders", {"order_id": order_id}, result=result, outcome="SUCCESS")
    
    return result


def get_pending_orders(db: Session, run_id: str = "", workflow: str = "") -> dict:
    """Get all orders with PENDING status."""
    orders = db.query(Order).filter(Order.status.in_(["PENDING", "PROCESSING"])).all()
    
    result = {
        "success": True,
        "orders": [
            {
                "order_id": o.order_id,
                "status": o.status,
                "priority": o.priority,
                "deadline": o.deadline.isoformat() if o.deadline else None,
                "destination": o.destination,
                "held_reason": o.held_reason
            }
            for o in orders
        ],
        "count": len(orders)
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_pending_orders", {}, result={"count": len(orders)}, outcome="SUCCESS")
    
    return result
