"""Exception management service.

Manages the lifecycle of order exceptions.
"""
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.exception import ExceptionRecord
from app.models.order import Order
from app.core.validation import validate_order_id, validate_status_transition
from app.services.audit_service import create_audit_entry, generate_run_id

def generate_exception_id() -> str:
    """Generate a unique exception ID."""
    return f"EXC-{uuid.uuid4().hex[:6].upper()}"

def create_exception(
    db: Session,
    order_id: str,
    exc_type: str,
    severity: str,
    description: str
) -> ExceptionRecord:
    """Creates an exception record."""
    validate_order_id(order_id)
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise ValueError(f"Order {order_id} not found")
        
    exception_id = generate_exception_id()
    
    exc = ExceptionRecord(
        exception_id=exception_id,
        order_id=order_id,
        type=exc_type,
        severity=severity,
        status="OPEN",
        description=description,
        created_at=datetime.now()
    )
    db.add(exc)
    db.commit()
    db.refresh(exc)
    
    create_audit_entry(
        db=db,
        run_id=generate_run_id(),
        workflow="exception_creation",
        tool_name="create_exception",
        input_data={"order_id": order_id, "type": exc_type, "severity": severity, "description": description},
        result={"exception_id": exception_id},
        outcome="SUCCESS"
    )
    
    return exc

def get_exception(db: Session, exception_id: str) -> ExceptionRecord | None:
    """Retrieve an exception by ID."""
    return db.query(ExceptionRecord).filter(ExceptionRecord.exception_id == exception_id).first()

def get_exceptions(db: Session, status: str | None = None) -> list[ExceptionRecord]:
    """List exceptions, optionally filtered by status."""
    query = db.query(ExceptionRecord)
    if status:
        query = query.filter(ExceptionRecord.status == status)
    return query.all()

def update_exception_status(
    db: Session,
    exception_id: str,
    new_status: str,
    resolution: str | None = None,
    evidence: str | None = None,
    policy_reference: str | None = None
) -> ExceptionRecord:
    """Updates exception status and details."""
    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError(f"Exception {exception_id} not found")
        
    validate_status_transition("exception", exc.status, new_status)
    
    old_status = exc.status
    exc.status = new_status
    if resolution:
        exc.resolution = resolution
    if evidence:
        exc.evidence = evidence
    
    if new_status == "RESOLVED":
        exc.resolved_at = datetime.now()
        
    db.commit()
    db.refresh(exc)
    
    create_audit_entry(
        db=db,
        run_id=generate_run_id(),
        workflow="exception_resolution",
        tool_name="update_exception_status",
        input_data={"exception_id": exception_id, "new_status": new_status, "resolution": resolution, "evidence": evidence},
        result={"status": new_status},
        policy_reference=policy_reference,
        state_changes={"old_status": old_status, "new_status": new_status},
        outcome="SUCCESS"
    )
    
    return exc

def get_exception_by_order(db: Session, order_id: str) -> list[ExceptionRecord]:
    """Find exceptions for a given order."""
    return db.query(ExceptionRecord).filter(ExceptionRecord.order_id == order_id).all()
