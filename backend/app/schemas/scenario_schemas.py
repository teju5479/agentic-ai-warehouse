from pydantic import BaseModel
from typing import Optional

class ScenarioSchema(BaseModel):
    scenario_id: str
    name: str
    description: str
    type: str
    expected_behavior: str
    affected_order: Optional[str] = None
    affected_sku: Optional[str] = None

class ScenarioRunResult(BaseModel):
    scenario_id: str
    name: str
    status: str  # RUNNING, COMPLETED, FAILED
    exception_id: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
