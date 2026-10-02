"""Picker management tools for agent workflows."""
from sqlalchemy.orm import Session
from app.models.picker import Picker
from app.services.audit_service import create_audit_entry
from app.core.validation import validate_picker_id
from app.core.feasibility import check_picker_capacity

def get_picker(db: Session, picker_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Get picker details."""
    validation = validate_picker_id(picker_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    picker = db.query(Picker).filter(Picker.picker_id == picker_id).first()
    if not picker:
        return {"success": False, "error": f"Picker {picker_id} not found"}
    
    result = {
        "success": True,
        "picker": {
            "picker_id": picker.picker_id,
            "name": picker.name,
            "availability": picker.availability,
            "capacity": picker.capacity,
            "current_workload": picker.current_workload
        }
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_picker", {"picker_id": picker_id}, result=result["picker"], outcome="SUCCESS")
    
    return result

def get_available_pickers(db: Session, run_id: str = "", workflow: str = "") -> dict:
    """Get all available pickers with remaining capacity."""
    pickers = db.query(Picker).filter(Picker.availability == "AVAILABLE").all()
    
    available_pickers = []
    for p in pickers:
        if p.capacity > p.current_workload:
            available_pickers.append({
                "picker_id": p.picker_id,
                "name": p.name,
                "availability": p.availability,
                "capacity": p.capacity,
                "current_workload": p.current_workload,
                "remaining_capacity": p.capacity - p.current_workload
            })
    
    result = {
        "success": True,
        "pickers": available_pickers,
        "count": len(available_pickers)
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_available_pickers", {}, result={"count": len(available_pickers)}, outcome="SUCCESS")
    
    return result

def update_picker_availability(db: Session, picker_id: str, new_availability: str, run_id: str = "", workflow: str = "") -> dict:
    """Update availability with validation and audit."""
    validation = validate_picker_id(picker_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
        
    if new_availability not in ["AVAILABLE", "UNAVAILABLE", "BUSY"]:
        return {"success": False, "error": f"Invalid availability status: {new_availability}"}
    
    picker = db.query(Picker).filter(Picker.picker_id == picker_id).first()
    if not picker:
        return {"success": False, "error": f"Picker {picker_id} not found"}
    
    old_status = picker.availability
    picker.availability = new_availability
    db.commit()
    
    result = {
        "success": True,
        "picker_id": picker_id,
        "old_status": old_status,
        "new_status": new_availability
    }
    
    if run_id:
        state_changes = {"picker": picker_id, "old_status": old_status, "new_status": new_availability}
        create_audit_entry(db, run_id, workflow, "update_picker_availability", {"picker_id": picker_id, "new_availability": new_availability}, state_changes=state_changes, outcome="SUCCESS")
    
    return result

def update_picker_workload(db: Session, picker_id: str, workload_change: int, run_id: str = "", workflow: str = "") -> dict:
    """Update workload with capacity check."""
    validation = validate_picker_id(picker_id)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    try:
        picker = db.query(Picker).filter(Picker.picker_id == picker_id).first()
        if not picker:
            return {"success": False, "error": f"Picker {picker_id} not found"}
        
        new_workload = picker.current_workload + workload_change
        
        if new_workload < 0:
            return {"success": False, "error": "Workload cannot be negative"}
            
        if new_workload > picker.capacity:
            return {"success": False, "error": f"Workload exceeds capacity ({picker.capacity})"}
        
        old_workload = picker.current_workload
        picker.current_workload = new_workload
        
        if picker.current_workload >= picker.capacity:
            picker.availability = "BUSY"
        elif picker.current_workload < picker.capacity and picker.availability == "BUSY":
            picker.availability = "AVAILABLE"
            
        db.commit()
        
        result = {
            "success": True,
            "picker_id": picker_id,
            "old_workload": old_workload,
            "new_workload": new_workload,
            "availability": picker.availability
        }
        
        if run_id:
            state_changes = {"picker": picker_id, "old_workload": old_workload, "new_workload": new_workload}
            create_audit_entry(db, run_id, workflow, "update_picker_workload", {"picker_id": picker_id, "workload_change": workload_change}, state_changes=state_changes, outcome="SUCCESS")
            
        return result
    except Exception as e:
        if run_id:
            create_audit_entry(db, run_id, workflow, "update_picker_workload", {"picker_id": picker_id, "workload_change": workload_change}, error=str(e), outcome="FAILURE")
        return {"success": False, "error": str(e)}
