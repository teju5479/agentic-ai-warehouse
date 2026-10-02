from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal
import json

class ExceptionSchema(BaseModel):
    exception_id: str
    order_id: str
    type: str
    status: str
    severity: str
    description: str
    evidence: Optional[dict] = None
    policy_reference: Optional[str] = None
    resolution: Optional[str] = None
    proposed_action: Optional[dict | str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def from_db(cls, exc):
        evidence = json.loads(exc.evidence) if isinstance(exc.evidence, str) else exc.evidence
        proposed_action = None
        if exc.proposed_action:
            try:
                proposed_action = json.loads(exc.proposed_action) if isinstance(exc.proposed_action, str) else exc.proposed_action
            except Exception:
                proposed_action = exc.proposed_action

        return cls(
            exception_id=exc.exception_id,
            order_id=exc.order_id,
            type=exc.type,
            status=exc.status,
            severity=exc.severity,
            description=exc.description,
            evidence=evidence,
            policy_reference=exc.policy_reference,
            resolution=exc.resolution,
            proposed_action=proposed_action,
            created_at=exc.created_at,
            resolved_at=exc.resolved_at
        )

class ExceptionResolveRequest(BaseModel):
    pass  # The resolver agent handles this

class ExceptionApproveRequest(BaseModel):
    pass  # Approval with no extra data needed

class ExceptionRejectRequest(BaseModel):
    reason: str = ""

class EscalationSchema(BaseModel):
    exception_id: str
    order_id: str
    issue: str
    evidence_checked: list[str]
    conflicts: list[str]
    policy_reference: str
    recommended_human_action: str
    actions_already_taken: list[str] = []
    current_state: str = "ESCALATED"
    unresolved_questions: list[str]

class ResolverDecision(BaseModel):
    decision: Literal["AUTONOMOUS", "CONFIRMATION_REQUIRED", "ESCALATE"]
    confidence_reason: str
    policy_id: Optional[str] = None
    evidence: list[str] = []
    proposed_action: Optional[str] = None
    escalation_reason: Optional[str] = None
    effect: Optional[str] = None
