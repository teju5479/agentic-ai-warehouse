"""Inventory management tools for agent workflows."""
from sqlalchemy.orm import Session
from app.models.inventory import Inventory
from app.models.order import OrderLine
from app.services.audit_service import create_audit_entry
from app.core.validation import validate_sku, validate_order_id
from app.core.feasibility import check_inventory_readiness


def get_inventory(db: Session, sku: str, run_id: str = "", workflow: str = "") -> dict:
    """Retrieve inventory for a SKU, validate available = on_hand - reserved."""
    validation = validate_sku(sku)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    inventory = db.query(Inventory).filter(Inventory.sku == sku).first()
    if not inventory:
        return {"success": False, "error": f"Inventory for SKU {sku} not found"}
    
    calculated_available = inventory.on_hand - inventory.reserved
    result = {
        "success": True,
        "inventory": {
            "sku": inventory.sku,
            "location_id": inventory.location_id,
            "on_hand": inventory.on_hand,
            "reserved": inventory.reserved,
            "available": calculated_available,
        }
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_inventory", {"sku": sku}, result=result["inventory"], outcome="SUCCESS")
    
    return result


def get_all_inventory(db: Session, run_id: str = "", workflow: str = "") -> dict:
    """Retrieve all inventory records."""
    records = db.query(Inventory).all()
    
    result = {
        "success": True,
        "inventory": [
            {
                "sku": i.sku,
                "location_id": i.location_id,
                "on_hand": i.on_hand,
                "reserved": i.reserved,
                "available": i.on_hand - i.reserved,
            }
            for i in records
        ],
        "count": len(records)
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_all_inventory", {}, result={"count": len(records)}, outcome="SUCCESS")
    
    return result


def check_order_inventory(db: Session, order_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Check inventory readiness for all lines in an order using deterministic feasibility engine."""
    validation = validate_order_id(order_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    # Get order lines
    lines = db.query(OrderLine).filter(OrderLine.order_id == order_id).all()
    if not lines:
        return {"success": False, "error": f"No order lines found for {order_id}"}
    
    order_lines_dicts = [
        {"sku": l.sku, "requested_qty": l.requested_qty, "picked_qty": l.picked_qty}
        for l in lines
    ]
    
    # Get inventory for all relevant SKUs
    skus = {l.sku for l in lines}
    inventory_records = db.query(Inventory).filter(Inventory.sku.in_(skus)).all()
    inventory_map = {
        r.sku: {"on_hand": r.on_hand, "reserved": r.reserved, "available": r.on_hand - r.reserved}
        for r in inventory_records
    }
    
    # Use deterministic feasibility engine
    readiness = check_inventory_readiness(order_lines_dicts, inventory_map)
    
    result = {
        "success": True,
        "order_id": order_id,
        "inventory_ready": readiness["ready"],
        "details": readiness["details"],
        "shortfalls": readiness["shortfalls"]
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "check_order_inventory", 
                          {"order_id": order_id}, result=result, outcome="SUCCESS")
    
    return result
