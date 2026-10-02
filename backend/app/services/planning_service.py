"""Shift planning service.

Manages shift plans, assignments, and replanning operations.
"""
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.plan import Plan, Assignment
from app.core.feasibility import validate_assignment
from app.services.audit_service import create_audit_entry, generate_run_id

def generate_plan_id() -> str:
    """Generate a unique plan ID."""
    return f"PLAN-{uuid.uuid4().hex[:6].upper()}"

def generate_assignment_id() -> str:
    """Generate a unique assignment ID."""
    return f"ASN-{uuid.uuid4().hex[:6].upper()}"

def validate_plan_assignments(db: Session, assignments: list[dict]):
    """Validates all assignments."""
    for asn in assignments:
        validate_assignment(db, asn.get("picker_id"), asn.get("order_id"))

def create_plan(db: Session, created_by: str, assignments_data: list[dict]) -> Plan:
    """Creates a new plan with assignments."""
    validate_plan_assignments(db, assignments_data)
    
    plan_id = generate_plan_id()
    plan = Plan(
        plan_id=plan_id,
        created_at=datetime.now(),
        created_by=created_by,
        status="ACTIVE"
    )
    db.add(plan)
    
    for asn in assignments_data:
        assignment = Assignment(
            assignment_id=generate_assignment_id(),
            plan_id=plan_id,
            order_id=asn.get("order_id"),
            picker_id=asn.get("picker_id"),
            status="PENDING",
            assigned_at=datetime.now()
        )
        db.add(assignment)
        
    db.commit()
    db.refresh(plan)
    
    create_audit_entry(
        db=db,
        run_id=generate_run_id(),
        workflow="plan_creation",
        tool_name="create_plan",
        input_data={"created_by": created_by, "assignments_count": len(assignments_data)},
        result={"plan_id": plan_id},
        outcome="SUCCESS"
    )
    
    return plan

def get_plan(db: Session, plan_id: str) -> Plan | None:
    """Retrieve a plan by ID."""
    return db.query(Plan).filter(Plan.plan_id == plan_id).first()

def get_plans(db: Session) -> list[Plan]:
    """List all plans."""
    return db.query(Plan).all()

def get_current_plan(db: Session) -> Plan | None:
    """Get the latest active plan."""
    return db.query(Plan).filter(Plan.status == "ACTIVE").order_by(Plan.created_at.desc()).first()

def create_replan(
    db: Session, 
    original_plan_id: str, 
    change_reason: str, 
    changed_assignments: list[dict], 
    created_by: str
) -> Plan:
    """Creates a new plan version, preserving completed/in-progress assignments."""
    original_plan = get_plan(db, original_plan_id)
    if not original_plan:
        raise ValueError(f"Plan {original_plan_id} not found")
        
    # Mark old plan as REPLACED
    original_plan.status = "REPLACED"
    
    # Create new plan
    new_plan_id = generate_plan_id()
    new_plan = Plan(
        plan_id=new_plan_id,
        version=original_plan.version + 1,
        created_at=datetime.now(),
        created_by=created_by,
        status="ACTIVE",
        parent_plan_id=original_plan_id
    )
    db.add(new_plan)
    
    # Process unchanged (in progress/completed) assignments from old plan
    for old_asn in original_plan.assignments:
        if old_asn.status in ("COMPLETED", "IN_PROGRESS"):
            new_asn = Assignment(
                assignment_id=generate_assignment_id(),
                plan_id=new_plan_id,
                order_id=old_asn.order_id,
                picker_id=old_asn.picker_id,
                status=old_asn.status,
                assigned_at=old_asn.assigned_at
            )
            db.add(new_asn)
            
    # Process changed/new assignments
    validate_plan_assignments(db, changed_assignments)
    for asn_data in changed_assignments:
        new_asn = Assignment(
            assignment_id=generate_assignment_id(),
            plan_id=new_plan_id,
            order_id=asn_data.get("order_id"),
            picker_id=asn_data.get("picker_id"),
            status="PENDING",
            assigned_at=datetime.now()
        )
        db.add(new_asn)
        
    db.commit()
    db.refresh(new_plan)
    
    create_audit_entry(
        db=db,
        run_id=generate_run_id(),
        workflow="plan_replanning",
        tool_name="create_replan",
        input_data={"original_plan_id": original_plan_id, "change_reason": change_reason},
        result={"new_plan_id": new_plan_id},
        outcome="SUCCESS"
    )
    
    return new_plan
