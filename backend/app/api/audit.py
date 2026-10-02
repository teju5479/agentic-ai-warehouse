from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.audit import AuditLog
from app.schemas.audit_schemas import AuditLogSchema

router = APIRouter(prefix="/api/audit", tags=["Audit"])

@router.get("", response_model=list[AuditLogSchema])
def list_audit_logs(
    workflow: str | None = None, 
    run_id: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if workflow:
        query = query.filter(AuditLog.workflow == workflow)
    if run_id:
        query = query.filter(AuditLog.run_id == run_id)
        
    limit_val = int(limit) if isinstance(limit, (int, str)) and str(limit).isdigit() else 100
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit_val).all()
    return [AuditLogSchema.from_db(l) for l in logs]

@router.get("/{run_id}", response_model=list[AuditLogSchema])
def get_audit_logs_for_run(run_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.run_id == run_id).order_by(AuditLog.timestamp.desc()).all()
    return [AuditLogSchema.from_db(l) for l in logs]
