"""Audit logging service.

Every important operation creates an audit record.
Never logs API keys or secrets.
"""
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def create_audit_entry(
    db: Session,
    run_id: str,
    workflow: str,
    tool_name: str,
    input_data: dict,
    result: dict | None = None,
    error: str | None = None,
    policy_reference: str | None = None,
    decision: str | None = None,
    proposed_action: str | None = None,
    approval_state: str | None = None,
    state_changes: dict | None = None,
    outcome: str = "SUCCESS"
) -> AuditLog:
    """Create an audit log entry."""
    entry = AuditLog(
        run_id=run_id,
        timestamp=datetime.now(),
        workflow=workflow,
        tool_name=tool_name,
        input_data=json.dumps(input_data) if input_data else "{}",
        result=json.dumps(result) if result else None,
        error=error,
        policy_reference=policy_reference,
        decision=decision,
        proposed_action=proposed_action,
        approval_state=approval_state,
        state_changes=json.dumps(state_changes) if state_changes else None,
        outcome=outcome
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_logs(db: Session, workflow: str | None = None, run_id: str | None = None, limit: int = 100) -> list[AuditLog]:
    """Retrieve audit logs with optional filtering."""
    query = db.query(AuditLog)
    if workflow:
        query = query.filter(AuditLog.workflow == workflow)
    if run_id:
        query = query.filter(AuditLog.run_id == run_id)
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()


def generate_run_id() -> str:
    """Generate a unique run ID."""
    return f"RUN-{uuid.uuid4().hex[:8].upper()}"
