"""Tests for business rules."""
from app.core.rules import (
    can_assign_order, can_picker_receive_work, requires_approval,
    determine_decision_type, check_stale_threshold
)


def test_pending_order_assignable():
    result = can_assign_order("PENDING")
    assert result["allowed"] is True

def test_blocked_order_not_assignable():
    result = can_assign_order("BLOCKED")
    assert result["allowed"] is False

def test_completed_order_not_assignable():
    result = can_assign_order("COMPLETED")
    assert result["allowed"] is False

def test_available_picker_can_work():
    result = can_picker_receive_work("AVAILABLE")
    assert result["allowed"] is True

def test_unavailable_picker_cannot_work():
    result = can_picker_receive_work("UNAVAILABLE")
    assert result["allowed"] is False

def test_cancel_requires_approval():
    result = requires_approval("cancel_order")
    assert result["required"] is True

def test_inventory_shortfall_autonomous():
    result = determine_decision_type("inventory_shortfall", {})
    assert result["decision_type"] == "AUTONOMOUS"

def test_duplicate_needs_confirmation():
    result = determine_decision_type("duplicate_order", {})
    assert result["decision_type"] == "CONFIRMATION_REQUIRED"

def test_conflict_needs_escalation():
    result = determine_decision_type("status_conflict", {})
    assert result["decision_type"] == "ESCALATE"

def test_stale_threshold():
    result = check_stale_threshold(14, 7)
    assert result["is_stale"] is True

def test_not_stale():
    result = check_stale_threshold(3, 7)
    assert result["is_stale"] is False
