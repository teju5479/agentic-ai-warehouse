"""Business rules enforcement.

These rules are enforced deterministically in Python code.
The LLM MUST NOT bypass these rules.
"""


def can_assign_order(order_status: str) -> dict:
    """Check if an order can be assigned based on its status."""
    assignable = ["PENDING", "PROCESSING"]
    if order_status in assignable:
        return {"allowed": True, "reason": f"Order status {order_status} is assignable"}
    return {"allowed": False, "reason": f"Order status {order_status} is not assignable. Only {assignable} orders can be assigned."}


def can_picker_receive_work(picker_availability: str) -> dict:
    """Check if a picker can receive new work."""
    if picker_availability == "AVAILABLE":
        return {"allowed": True, "reason": "Picker is available"}
    return {"allowed": False, "reason": f"Picker is {picker_availability}. Only AVAILABLE pickers can receive work (SOP-006)."}


def requires_approval(action: str) -> dict:
    """Check if an action requires explicit human approval."""
    approval_required = {
        "cancel_order": "SOP-003: Orders cannot be cancelled without explicit approval",
        "merge_orders": "SOP-003: Orders cannot be merged without explicit approval",
        "delete_order": "SOP-003: Orders cannot be deleted without explicit approval",
        "override_inventory": "SOP-008: Consequential actions require policy-supported evidence",
        "force_assignment": "SOP-005: Picker capacity limits must be respected",
    }
    
    if action in approval_required:
        return {"required": True, "policy": approval_required[action]}
    return {"required": False, "policy": None}


def is_duplicate_action(existing_actions: list[str], proposed_action: str) -> dict:
    """Check if a proposed action would duplicate an existing one."""
    if proposed_action in existing_actions:
        return {"is_duplicate": True, "reason": f"Action '{proposed_action}' has already been performed"}
    return {"is_duplicate": False, "reason": None}


def check_stale_threshold(days_since_update: float, threshold_days: int = 7) -> dict:
    """Check if a shipment/record is stale."""
    is_stale = days_since_update > threshold_days
    return {
        "is_stale": is_stale,
        "days_since_update": round(days_since_update, 1),
        "threshold_days": threshold_days,
        "reason": f"Record is stale ({round(days_since_update, 1)} days, threshold: {threshold_days})" if is_stale
                 else f"Record is current ({round(days_since_update, 1)} days, threshold: {threshold_days})"
    }


def determine_decision_type(exception_type: str, evidence: dict) -> dict:
    """Determine whether a resolution should be autonomous, need confirmation, or escalation.
    
    This is a rule-based pre-filter. The LLM may add additional context.
    """
    # Escalation scenarios - conflicting/ambiguous data
    escalation_types = ["status_conflict", "conflicting_destination", "missing_inventory"]
    if exception_type in escalation_types:
        return {
            "decision_type": "ESCALATE",
            "reason": f"Exception type '{exception_type}' involves conflicting or ambiguous data requiring human review",
            "policy": "SOP-002"
        }
    
    # Confirmation required - destructive actions
    confirmation_types = ["duplicate_order"]
    if exception_type in confirmation_types:
        return {
            "decision_type": "CONFIRMATION_REQUIRED",
            "reason": f"Exception type '{exception_type}' may require destructive action needing approval",
            "policy": "SOP-003"
        }
    
    # Autonomous - safe actions
    autonomous_types = ["inventory_shortfall", "invalid_quantity", "stale_shipment"]
    if exception_type in autonomous_types:
        return {
            "decision_type": "AUTONOMOUS",
            "reason": f"Exception type '{exception_type}' can be resolved with safe, policy-supported actions",
            "policy": "SOP-004" if exception_type == "inventory_shortfall" else "SOP-008"
        }
    
    # Default to escalation for unknown types
    return {
        "decision_type": "ESCALATE",
        "reason": f"No specific rule for exception type '{exception_type}'. Escalating per SOP-010.",
        "policy": "SOP-010"
    }
