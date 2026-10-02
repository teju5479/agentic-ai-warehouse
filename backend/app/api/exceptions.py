from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.exception import ExceptionRecord
from app.schemas.exception_schemas import ExceptionSchema

router = APIRouter(prefix="/api/exceptions", tags=["Exceptions"])


@router.get("", response_model=list[ExceptionSchema])
def list_exceptions(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ExceptionRecord)
    if status:
        query = query.filter(ExceptionRecord.status == status)
    exceptions = query.all()
    return [ExceptionSchema.from_db(e) for e in exceptions]


@router.get("/{exception_id}")
def get_exception(exception_id: str, db: Session = Depends(get_db)):
    exc = db.query(ExceptionRecord).filter(ExceptionRecord.exception_id == exception_id).first()
    if not exc:
        raise HTTPException(404, f"Exception {exception_id} not found")
    return ExceptionSchema.from_db(exc)


@router.post("/{exception_id}/resolve")
async def resolve_exception(exception_id: str, db: Session = Depends(get_db)):
    """Run the exception resolver agent on this exception."""
    from app.graph.exception_graph import run_exception_resolver
    try:
        result = run_exception_resolver(exception_id)
        return result
    except Exception as e:
        raise HTTPException(500, f"Resolver failed: {str(e)}")


@router.post("/{exception_id}/approve")
def approve_exception(exception_id: str, db: Session = Depends(get_db)):
    """Approve a pending action for an exception."""
    from app.graph.exception_graph import approve_exception_action
    try:
        result = approve_exception_action(exception_id)
        return result
    except Exception as e:
        raise HTTPException(500, f"Approval failed: {str(e)}")


@router.post("/{exception_id}/reject")
def reject_exception(exception_id: str, db: Session = Depends(get_db)):
    """Reject a pending action for an exception."""
    from app.graph.exception_graph import reject_exception_action
    try:
        result = reject_exception_action(exception_id)
        return result
    except Exception as e:
        raise HTTPException(500, f"Rejection failed: {str(e)}")
