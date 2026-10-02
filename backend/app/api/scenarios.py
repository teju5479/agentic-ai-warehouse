from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.scenario_service import get_scenarios, get_scenario, reset_database, run_scenario

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.get("")
def list_scenarios():
    return get_scenarios()


@router.post("/reset")
def reset_env(db: Session = Depends(get_db)):
    """Reset database to initial seeded state."""
    try:
        reset_database(db)
        return {"status": "success", "message": "Database reset to initial state"}
    except Exception as e:
        raise HTTPException(500, f"Reset failed: {str(e)}")


@router.post("/{scenario_id}/run")
async def run_scenario_endpoint(scenario_id: str, db: Session = Depends(get_db)):
    """Run a specific scenario."""
    try:
        result = run_scenario(db, scenario_id)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Scenario failed: {str(e)}")
