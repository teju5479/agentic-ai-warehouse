from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import json

def safe_json_parse(val):
    if not val:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {"raw": str(val)}

class AuditLogSchema(BaseModel):
    id: int
    run_id: str
    timestamp: Optional[datetime] = None
    workflow: str
    tool_name: str
    input_data: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    policy_reference: Optional[str] = None
    decision: Optional[str] = None
    proposed_action: Optional[str] = None
    approval_state: Optional[str] = None
    state_changes: Optional[dict] = None
    outcome: str
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def from_db(cls, log):
        return cls(
            id=log.id,
            run_id=log.run_id,
            timestamp=log.timestamp,
            workflow=log.workflow,
            tool_name=log.tool_name,
            input_data=safe_json_parse(log.input_data),
            result=safe_json_parse(log.result),
            error=log.error,
            policy_reference=log.policy_reference,
            decision=log.decision,
            proposed_action=log.proposed_action,
            approval_state=log.approval_state,
            state_changes=safe_json_parse(log.state_changes),
            outcome=log.outcome
        )
