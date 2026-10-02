from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

class AssignmentSchema(BaseModel):
    order_id: str
    picker_id: Optional[str] = None
    sequence: int = 0
    workload: int = 0
    status: str = "PENDING"
    reason: Optional[str] = None
    inventory_ready: bool = True
    deadline: Optional[str] = None
    feasible: bool = True
    
    model_config = {"from_attributes": True}

class PlanSchema(BaseModel):
    plan_id: str
    version: int
    status: str
    created_at: Optional[datetime] = None
    created_by: str
    assignments: list[AssignmentSchema] = []
    
    model_config = {"from_attributes": True}

class PlannerRunRequest(BaseModel):
    pass

class ReplanRequest(BaseModel):
    change_type: Literal["picker_unavailable", "urgent_order"]
    change_details: dict = {}

class PlannerExplanation(BaseModel):
    prioritized_orders: list[str] = []
    blocked_orders: list[str] = []
    infeasible_orders: list[str] = []
    rationale: list[str] = []
    changes: list[str] = []
