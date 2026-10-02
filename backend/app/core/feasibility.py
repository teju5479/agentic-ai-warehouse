"""Deterministic feasibility engine for warehouse operations.

All capacity, inventory, and assignment decisions are made here in deterministic
Python code. The LLM must NEVER be the final authority on these calculations.
"""
from datetime import datetime, timedelta
from typing import Any


def check_inventory_readiness(order_lines: list[dict], inventory: dict[str, dict]) -> dict:
    """Check if all SKUs for an order have sufficient available inventory.
    
    Args:
        order_lines: List of {sku, requested_qty, picked_qty, status}
        inventory: Dict mapping SKU -> {on_hand, reserved, available}
    
    Returns:
        {ready: bool, details: [{sku, requested, available, sufficient}], shortfalls: [...]}
    """
    details = []
    shortfalls = []
    all_ready = True
    
    for line in order_lines:
        sku = line["sku"]
        requested = line["requested_qty"]
        remaining_needed = requested - line.get("picked_qty", 0)
        
        if remaining_needed <= 0:
            details.append({"sku": sku, "requested": requested, "remaining_needed": 0, "available": 0, "sufficient": True, "note": "Already picked"})
            continue
            
        inv = inventory.get(sku)
        if inv is None:
            all_ready = False
            detail = {"sku": sku, "requested": requested, "remaining_needed": remaining_needed, "available": 0, "sufficient": False, "note": "No inventory record found"}
            details.append(detail)
            shortfalls.append(detail)
            continue
        
        available = inv.get("available", 0)
        sufficient = remaining_needed <= available
        
        detail = {
            "sku": sku,
            "requested": requested,
            "remaining_needed": remaining_needed,
            "available": available,
            "sufficient": sufficient,
            "shortfall": max(0, remaining_needed - available) if not sufficient else 0
        }
        details.append(detail)
        
        if not sufficient:
            all_ready = False
            shortfalls.append(detail)
    
    return {
        "ready": all_ready,
        "details": details,
        "shortfalls": shortfalls
    }


def check_picker_capacity(picker: dict, required_workload: int) -> dict:
    """Check if a picker has sufficient remaining capacity.
    
    Args:
        picker: {picker_id, capacity, current_workload, availability}
        required_workload: Workload units needed
    
    Returns:
        {feasible: bool, remaining_capacity: int, required_workload: int, reason: str}
    """
    if picker.get("availability") != "AVAILABLE":
        return {
            "feasible": False,
            "remaining_capacity": 0,
            "required_workload": required_workload,
            "reason": f"Picker {picker['picker_id']} is {picker.get('availability', 'UNKNOWN')}, cannot assign work"
        }
    
    remaining = picker["capacity"] - picker["current_workload"]
    feasible = required_workload <= remaining
    
    return {
        "feasible": feasible,
        "remaining_capacity": remaining,
        "required_workload": required_workload,
        "reason": f"Capacity OK ({remaining} remaining, {required_workload} needed)" if feasible 
                 else f"Insufficient capacity ({remaining} remaining, {required_workload} needed)"
    }


def check_order_feasibility(order: dict, order_lines: list[dict], inventory: dict[str, dict]) -> dict:
    """Full feasibility check for an order.
    
    Returns:
        {feasible: bool, reasons: [...], inventory_ready: bool, status_ok: bool, data_valid: bool}
    """
    reasons = []
    feasible = True
    
    # Check order status
    blocked_statuses = ["BLOCKED", "CANCELLED", "COMPLETED", "HELD"]
    status_ok = order.get("status") not in blocked_statuses
    if not status_ok:
        feasible = False
        reasons.append(f"Order status is {order['status']} - cannot be assigned")
    
    # Check for invalid quantities
    data_valid = True
    for line in order_lines:
        if line["requested_qty"] <= 0:
            data_valid = False
            feasible = False
            reasons.append(f"Invalid quantity for {line['sku']}: {line['requested_qty']}")
    
    # Check inventory
    inv_check = check_inventory_readiness(order_lines, inventory)
    inventory_ready = inv_check["ready"]
    if not inventory_ready:
        feasible = False
        for sf in inv_check["shortfalls"]:
            reasons.append(f"Inventory shortfall for {sf['sku']}: need {sf['remaining_needed']}, available {sf['available']}")
    
    return {
        "feasible": feasible,
        "reasons": reasons if reasons else ["All checks passed"],
        "inventory_ready": inventory_ready,
        "inventory_details": inv_check["details"],
        "status_ok": status_ok,
        "data_valid": data_valid
    }


def calculate_workload(order_lines: list[dict]) -> int:
    """Calculate total workload for an order based on its lines.
    
    Simple heuristic: sum of remaining quantities to pick.
    """
    total = 0
    for line in order_lines:
        remaining = line["requested_qty"] - line.get("picked_qty", 0)
        if remaining > 0:
            total += remaining
    return total


def calculate_deadline_urgency(deadline: datetime | str | None) -> dict:
    """Calculate urgency score based on deadline proximity.
    
    Returns:
        {urgency_score: float, hours_remaining: float, is_overdue: bool, category: str}
    
    Score: higher = more urgent
        0-1h: 100
        1-2h: 80
        2-4h: 60
        4-8h: 40
        8-24h: 20
        24h+: 10
        overdue: 120
    """
    if deadline is None:
        return {"urgency_score": 10, "hours_remaining": 999, "is_overdue": False, "category": "NO_DEADLINE"}
    
    if isinstance(deadline, str):
        deadline = datetime.fromisoformat(deadline)
    
    now = datetime.now()
    delta = deadline - now
    hours_remaining = delta.total_seconds() / 3600
    
    if hours_remaining < 0:
        return {"urgency_score": 120, "hours_remaining": hours_remaining, "is_overdue": True, "category": "OVERDUE"}
    elif hours_remaining <= 1:
        return {"urgency_score": 100, "hours_remaining": hours_remaining, "is_overdue": False, "category": "CRITICAL"}
    elif hours_remaining <= 2:
        return {"urgency_score": 80, "hours_remaining": hours_remaining, "is_overdue": False, "category": "URGENT"}
    elif hours_remaining <= 4:
        return {"urgency_score": 60, "hours_remaining": hours_remaining, "is_overdue": False, "category": "HIGH"}
    elif hours_remaining <= 8:
        return {"urgency_score": 40, "hours_remaining": hours_remaining, "is_overdue": False, "category": "MEDIUM"}
    elif hours_remaining <= 24:
        return {"urgency_score": 20, "hours_remaining": hours_remaining, "is_overdue": False, "category": "LOW"}
    else:
        return {"urgency_score": 10, "hours_remaining": hours_remaining, "is_overdue": False, "category": "MINIMAL"}


def validate_assignment(order: dict, order_lines: list[dict], picker: dict, inventory: dict[str, dict]) -> dict:
    """Full validation of an order-to-picker assignment.
    
    Returns:
        {valid: bool, errors: [...], workload: int, capacity_check: dict, feasibility_check: dict}
    """
    errors = []
    
    # Check order feasibility
    feas = check_order_feasibility(order, order_lines, inventory)
    if not feas["feasible"]:
        errors.extend(feas["reasons"])
    
    # Calculate workload
    workload = calculate_workload(order_lines)
    
    # Check picker capacity
    cap = check_picker_capacity(picker, workload)
    if not cap["feasible"]:
        errors.append(cap["reason"])
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "workload": workload,
        "capacity_check": cap,
        "feasibility_check": feas
    }
