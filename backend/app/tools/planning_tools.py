"""Planning tools for agent workflows."""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.plan import Plan, Assignment
from app.core.feasibility import validate_assignment as validate_assignment_feasibility
from app.services.audit_service import create_audit_entry

def assign_order(db: Session, order_id: str, picker_id: str, sequence: int, run_id: str = "", workflow: str = "") -> dict:
    """Full validated assignment with feasibility check."""
    feasibility = validate_assignment_feasibility(db, order_id, picker_id)
    
    if not feasibility.get("valid", False):
        if run_id:
            create_audit_entry(db, run_id, workflow, "assign_order", 
                              {"order_id": order_id, "picker_id": picker_id}, 
                              error=feasibility.get("error", "Unknown error"), outcome="FAILURE")
        return {"success": False, "error": feasibility.get("error", "Assignment not feasible")}
        
    result = {
        "success": True,
        "assignment": {
            "order_id": order_id,
            "picker_id": picker_id,
            "sequence": sequence
        }
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "assign_order", 
                          {"order_id": order_id, "picker_id": picker_id, "sequence": sequence}, 
                          result=result, outcome="SUCCESS")
                          
    return result

def create_plan(db: Session, assignments: list, created_by: str, run_id: str = "", workflow: str = "", version: int = 1, parent_plan_id: str = "", supersede_plan_id: str = "") -> dict:
    """Create a complete plan with all validated assignments."""
    plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        if supersede_plan_id:
            old_plan = db.query(Plan).filter(Plan.plan_id == supersede_plan_id).first()
            if old_plan:
                old_plan.status = "SUPERSEDED"

        new_plan = Plan(
            plan_id=plan_id,
            version=version,
            parent_plan_id=parent_plan_id or None,
            status="ACTIVE",
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        db.add(new_plan)
        
        for idx, assign_data in enumerate(assignments):
            assignment = Assignment(
                plan_id=plan_id,
                order_id=assign_data.get("order_id"),
                picker_id=assign_data.get("picker_id"),
                sequence=assign_data.get("sequence", idx + 1),
                workload=assign_data.get("workload", 0),
                reason=assign_data.get("reason", ""),
                status=assign_data.get("status", "PENDING")
            )
            db.add(assignment)
            
        db.commit()
        
        result = {
            "success": True,
            "plan_id": plan_id,
            "assignment_count": len(assignments),
            "version": version,
            "parent_plan_id": parent_plan_id or None
        }
        
        if run_id:
            create_audit_entry(db, run_id, workflow, "create_plan", 
                              {"assignment_count": len(assignments)}, 
                              result=result, outcome="SUCCESS")
                              
        return result
    except Exception as e:
        db.rollback()
        if run_id:
            create_audit_entry(db, run_id, workflow, "create_plan", {}, error=str(e), outcome="FAILURE")
        return {"success": False, "error": str(e)}

def get_current_plan(db: Session, run_id: str = "", workflow: str = "") -> dict:
    """Get latest active plan."""
    plan = db.query(Plan).filter(Plan.status == "ACTIVE").order_by(Plan.created_at.desc()).first()
    
    if not plan:
        return {"success": False, "error": "No active plan found"}
        
    assignments = db.query(Assignment).filter(Assignment.plan_id == plan.plan_id).all()
    
    result = {
        "success": True,
        "plan": {
            "plan_id": plan.plan_id,
            "version": plan.version,
            "parent_plan_id": plan.parent_plan_id,
            "status": plan.status,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "created_by": plan.created_by,
            "assignments": [
                {
                    "order_id": a.order_id,
                    "picker_id": a.picker_id,
                    "sequence": a.sequence,
                    "workload": a.workload,
                    "reason": a.reason,
                    "status": a.status
                }
                for a in assignments
            ]
        }
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_current_plan", {}, result={"plan_id": plan.plan_id}, outcome="SUCCESS")
        
    return result

def replan(db: Session, original_plan_id: str, change_reason: str, run_id: str = "", workflow: str = "") -> dict:
    """Create a new plan version preserving completed/in-progress work."""
    old_plan = db.query(Plan).filter(Plan.plan_id == original_plan_id).first()
    if not old_plan:
        return {"success": False, "error": f"Plan {original_plan_id} not found"}
        
    try:
        old_plan.status = "SUPERSEDED"
        
        new_plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
        new_plan = Plan(
            plan_id=new_plan_id,
            version=old_plan.version + 1,
            parent_plan_id=original_plan_id,
            status="ACTIVE",
            created_by="system_replan",
            created_at=datetime.utcnow()
        )
        db.add(new_plan)
        
        # Move assignments
        assignments = db.query(Assignment).filter(Assignment.plan_id == original_plan_id).all()
        moved_count = 0
        
        for a in assignments:
            if a.status in ["COMPLETED", "IN_PROGRESS"]:
                new_a = Assignment(
                    plan_id=new_plan_id,
                    order_id=a.order_id,
                    picker_id=a.picker_id,
                    sequence=a.sequence,
                    workload=a.workload,
                    reason=a.reason,
                    status=a.status
                )
                db.add(new_a)
                moved_count += 1
                
        db.commit()
        
        result = {
            "success": True,
            "old_plan_id": original_plan_id,
            "new_plan_id": new_plan_id,
            "preserved_assignments": moved_count,
            "reason": change_reason
        }
        
        if run_id:
            create_audit_entry(db, run_id, workflow, "replan", 
                              {"original_plan_id": original_plan_id, "reason": change_reason}, 
                              result=result, outcome="SUCCESS")
                              
        return result
    except Exception as e:
        db.rollback()
        if run_id:
            create_audit_entry(db, run_id, workflow, "replan", 
                              {"original_plan_id": original_plan_id}, error=str(e), outcome="FAILURE")
        return {"success": False, "error": str(e)}
