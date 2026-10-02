"""Tests for deterministic feasibility engine."""
from app.core.feasibility import (
    check_inventory_readiness, check_picker_capacity,
    check_order_feasibility, calculate_workload, calculate_deadline_urgency
)
from datetime import datetime, timedelta


def test_inventory_shortfall():
    """EXC-001: Order requires more inventory than available."""
    order_lines = [{"sku": "SKU-005", "requested_qty": 10, "picked_qty": 0}]
    inventory = {"SKU-005": {"on_hand": 8, "reserved": 2, "available": 6}}
    result = check_inventory_readiness(order_lines, inventory)
    assert result["ready"] is False
    assert len(result["shortfalls"]) == 1
    assert result["shortfalls"][0]["sku"] == "SKU-005"


def test_inventory_sufficient():
    order_lines = [{"sku": "SKU-001", "requested_qty": 5, "picked_qty": 0}]
    inventory = {"SKU-001": {"on_hand": 50, "reserved": 10, "available": 40}}
    result = check_inventory_readiness(order_lines, inventory)
    assert result["ready"] is True
    assert len(result["shortfalls"]) == 0


def test_missing_inventory_record():
    """EXC-007: SKU has no inventory record."""
    order_lines = [{"sku": "SKU-011", "requested_qty": 5, "picked_qty": 0}]
    inventory = {}  # No record
    result = check_inventory_readiness(order_lines, inventory)
    assert result["ready"] is False


def test_picker_capacity_sufficient():
    picker = {"picker_id": "PICK-001", "capacity": 20, "current_workload": 5, "availability": "AVAILABLE"}
    result = check_picker_capacity(picker, 10)
    assert result["feasible"] is True
    assert result["remaining_capacity"] == 15


def test_picker_capacity_exceeded():
    picker = {"picker_id": "PICK-001", "capacity": 20, "current_workload": 18, "availability": "AVAILABLE"}
    result = check_picker_capacity(picker, 5)
    assert result["feasible"] is False


def test_unavailable_picker():
    picker = {"picker_id": "PICK-004", "capacity": 20, "current_workload": 0, "availability": "UNAVAILABLE"}
    result = check_picker_capacity(picker, 5)
    assert result["feasible"] is False


def test_blocked_order_not_feasible():
    order = {"order_id": "ORD-1004", "status": "BLOCKED"}
    order_lines = [{"sku": "SKU-005", "requested_qty": 10, "picked_qty": 0}]
    inventory = {"SKU-005": {"available": 6}}
    result = check_order_feasibility(order, order_lines, inventory)
    assert result["feasible"] is False
    assert result["status_ok"] is False


def test_invalid_quantity_not_feasible():
    """EXC-004: Negative quantity."""
    order = {"order_id": "ORD-1008", "status": "PENDING"}
    order_lines = [{"sku": "SKU-004", "requested_qty": -2, "picked_qty": 0}]
    inventory = {"SKU-004": {"available": 13}}
    result = check_order_feasibility(order, order_lines, inventory)
    assert result["feasible"] is False
    assert result["data_valid"] is False


def test_calculate_workload():
    order_lines = [
        {"sku": "SKU-001", "requested_qty": 5, "picked_qty": 2},
        {"sku": "SKU-003", "requested_qty": 3, "picked_qty": 0}
    ]
    workload = calculate_workload(order_lines)
    assert workload == 6  # (5-2) + (3-0)


def test_deadline_urgency_overdue():
    deadline = datetime.now() - timedelta(hours=2)
    result = calculate_deadline_urgency(deadline)
    assert result["is_overdue"] is True
    assert result["urgency_score"] == 120


def test_deadline_urgency_critical():
    deadline = datetime.now() + timedelta(minutes=30)
    result = calculate_deadline_urgency(deadline)
    assert result["category"] == "CRITICAL"
    assert result["urgency_score"] == 100
