from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.plan import Plan, Assignment
from app.schemas.plan_schemas import PlanSchema, AssignmentSchema, ReplanRequest

router = APIRouter(prefix="/api/planner", tags=["Planner"])


@router.post("/run")
async def run_planner(db: Session = Depends(get_db)):
    """Run the shift planner to create a new plan."""
    from app.graph.planner_graph import run_shift_planner
    try:
        result = run_shift_planner()
        return result
    except Exception as e:
        raise HTTPException(500, f"Planner failed: {str(e)}")


@router.get("/plans", response_model=list[PlanSchema])
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).order_by(Plan.created_at.desc()).all()
    result = []
    for plan in plans:
        assignments = db.query(Assignment).filter(Assignment.plan_id == plan.plan_id).all()
        plan_data = PlanSchema.model_validate(plan)
        plan_data.assignments = [AssignmentSchema.model_validate(a) for a in assignments]
        result.append(plan_data)
    return result


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(404, f"Plan {plan_id} not found")
    assignments = db.query(Assignment).filter(Assignment.plan_id == plan_id).all()
    return {
        **PlanSchema.model_validate(plan).model_dump(),
        "assignments": [AssignmentSchema.model_validate(a).model_dump() for a in assignments]
    }


@router.post("/replan")
async def replan(request: ReplanRequest, db: Session = Depends(get_db)):
    """Run replanning after a change event."""
    from app.graph.planner_graph import run_replan
    try:
        result = run_replan(request.change_type, request.change_details)
        return result
    except Exception as e:
        raise HTTPException(500, f"Replan failed: {str(e)}")
