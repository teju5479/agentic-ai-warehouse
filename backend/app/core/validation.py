"""Input validation for warehouse operations."""
from typing import Any


def validate_order_id(order_id: str) -> dict:
    """Validate order ID format (ORD-XXXX)."""
    if not order_id or not isinstance(order_id, str):
        return {"valid": False, "error": "Order ID must be a non-empty string"}
    if not order_id.startswith("ORD-"):
        return {"valid": False, "error": f"Invalid order ID format: {order_id}. Expected ORD-XXXX"}
    return {"valid": True, "error": None}


def validate_picker_id(picker_id: str) -> dict:
    """Validate picker ID format (PICK-XXX)."""
    if not picker_id or not isinstance(picker_id, str):
        return {"valid": False, "error": "Picker ID must be a non-empty string"}
    if not picker_id.startswith("PICK-"):
        return {"valid": False, "error": f"Invalid picker ID format: {picker_id}. Expected PICK-XXX"}
    return {"valid": True, "error": None}


def validate_sku(sku: str) -> dict:
    """Validate SKU format."""
    if not sku or not isinstance(sku, str):
        return {"valid": False, "error": "SKU must be a non-empty string"}
    if not sku.startswith("SKU-"):
        return {"valid": False, "error": f"Invalid SKU format: {sku}. Expected SKU-XXX"}
    return {"valid": True, "error": None}


def validate_quantity(qty: int, field_name: str = "quantity") -> dict:
    """Validate that quantity is a positive integer."""
    if not isinstance(qty, int):
        return {"valid": False, "error": f"{field_name} must be an integer"}
    if qty < 0:
        return {"valid": False, "error": f"{field_name} cannot be negative: {qty}"}
    return {"valid": True, "error": None}


def validate_status_transition(current_status: str, new_status: str, entity_type: str = "order") -> dict:
    """Validate state transitions."""
    valid_transitions = {
        "order": {
            "PENDING": ["PROCESSING", "BLOCKED", "CANCELLED", "HELD"],
            "PROCESSING": ["COMPLETED", "BLOCKED", "HELD", "CANCELLED"],
            "BLOCKED": ["PENDING", "CANCELLED", "HELD"],
            "HELD": ["PENDING", "PROCESSING", "CANCELLED"],
            "COMPLETED": [],  # Terminal state
            "CANCELLED": [],  # Terminal state
        },
        "exception": {
            "OPEN": ["INVESTIGATING", "RESOLVED", "ESCALATED"],
            "INVESTIGATING": ["RESOLVED", "ESCALATED", "WAITING_FOR_APPROVAL"],
            "WAITING_FOR_APPROVAL": ["RESOLVED", "ESCALATED", "REJECTED"],
            "ESCALATED": ["RESOLVED"],
            "RESOLVED": [],
            "REJECTED": ["OPEN", "INVESTIGATING"],
        },
        "assignment": {
            "PENDING": ["IN_PROGRESS", "CANCELLED", "REASSIGNED"],
            "IN_PROGRESS": ["COMPLETED", "CANCELLED"],
            "COMPLETED": [],
            "CANCELLED": [],
            "REASSIGNED": [],
        }
    }
    
    transitions = valid_transitions.get(entity_type, {})
    allowed = transitions.get(current_status, [])
    
    if new_status in allowed:
        return {"valid": True, "error": None}
    return {
        "valid": False, 
        "error": f"Invalid {entity_type} status transition: {current_status} -> {new_status}. Allowed: {allowed}"
    }
