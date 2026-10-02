"""Tests for input validation."""
from app.core.validation import (
    validate_order_id, validate_picker_id, validate_sku, 
    validate_quantity, validate_status_transition
)


def test_valid_order_id():
    result = validate_order_id("ORD-1001")
    assert result["valid"] is True

def test_invalid_order_id():
    result = validate_order_id("INVALID")
    assert result["valid"] is False

def test_empty_order_id():
    result = validate_order_id("")
    assert result["valid"] is False

def test_valid_picker_id():
    result = validate_picker_id("PICK-001")
    assert result["valid"] is True

def test_invalid_picker_id():
    result = validate_picker_id("WORKER-1")
    assert result["valid"] is False

def test_valid_sku():
    result = validate_sku("SKU-001")
    assert result["valid"] is True

def test_invalid_quantity():
    result = validate_quantity(-2, "requested_qty")
    assert result["valid"] is False

def test_valid_quantity():
    result = validate_quantity(10, "requested_qty")
    assert result["valid"] is True

def test_valid_status_transition():
    result = validate_status_transition("PENDING", "PROCESSING", "order")
    assert result["valid"] is True

def test_invalid_status_transition():
    result = validate_status_transition("COMPLETED", "PENDING", "order")
    assert result["valid"] is False

def test_blocked_to_pending():
    result = validate_status_transition("BLOCKED", "PENDING", "order")
    assert result["valid"] is True
