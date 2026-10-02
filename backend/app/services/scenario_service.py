"""Scenario management service.

Handles test scenarios and database reseeding.
"""
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.tools.exception_tools import create_exception_record
from app.seed.seed_database import seed_database as do_seed


SCENARIOS_FILE = Path(__file__).parent.parent / "seed" / "scenarios.json"


def get_scenarios() -> list[dict]:
    """Load and return scenarios from scenarios.json."""
    if not SCENARIOS_FILE.exists():
        return []
    with open(SCENARIOS_FILE, "r") as f:
        return json.load(f)


def get_scenario(scenario_id: str) -> dict | None:
    """Get a specific scenario by ID."""
    scenarios = get_scenarios()
    for s in scenarios:
        if s.get("scenario_id") == scenario_id:
            return s
    return None


def reset_database(db: Session):
    """Resets the database to initial seeded state."""
    do_seed(db)


def run_scenario(db: Session, scenario_id: str) -> dict:
    """Sets up the scenario by creating the relevant exception record.
    
    For exception scenarios, creates an ExceptionRecord.
    For planning scenarios, just returns the scenario info.
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")
    
    scenario_type = scenario.get("type", "")
    
    # Planning scenarios don't create exceptions
    if scenario_type in ["planning", "replanning"]:
        return {
            "scenario_id": scenario_id,
            "name": scenario.get("name"),
            "status": "READY",
            "type": scenario_type,
            "message": scenario.get("description"),
        }
    
    # Exception scenarios - create an exception record
    affected_order = scenario.get("affected_order", "ORD-TEST")
    
    # Map scenario types to severity
    severity_map = {
        "inventory_shortfall": "HIGH",
        "duplicate_order": "MEDIUM",
        "status_conflict": "HIGH",
        "invalid_quantity": "MEDIUM",
        "stale_shipment": "MEDIUM",
        "conflicting_destination": "HIGH",
        "missing_inventory": "HIGH",
    }
    
    severity = severity_map.get(scenario_type, "MEDIUM")
    description = scenario.get("description", f"Generated for scenario {scenario_id}")
    
    result = create_exception_record(
        db, 
        order_id=affected_order,
        exc_type=scenario_type,
        severity=severity,
        description=description,
        run_id=f"SCENARIO-{scenario_id}",
        workflow="scenario_runner"
    )
    
    if result.get("success"):
        return {
            "scenario_id": scenario_id,
            "name": scenario.get("name"),
            "status": "CREATED",
            "exception_id": result["exception_id"],
            "type": scenario_type,
            "affected_order": affected_order,
            "message": f"Exception created. Use POST /api/exceptions/{result['exception_id']}/resolve to run the resolver."
        }
    else:
        return {
            "scenario_id": scenario_id,
            "status": "FAILED",
            "error": result.get("error", "Unknown error")
        }
