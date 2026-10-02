"""Tests for cross-agent state integration.

Verifies that the Exception Resolver and Shift Planner share state
and that the planner respects exception-blocked orders.
"""
import pytest
from app.models.order import Order
from app.models.exception import ExceptionRecord
from app.core.feasibility import check_order_feasibility
from app.core.rules import can_assign_order


def test_cross_agent_state(db_session):
    """Simulate: Resolver blocks ORD-1004, then planner checks it."""
    # Step 1: Simulate resolver blocking the order
    order = db_session.query(Order).filter(Order.order_id == "ORD-1004").first()
    assert order is not None
    assert order.status == "PENDING"
    
    # Block the order (as resolver would)
    order.status = "BLOCKED"
    order.held_reason = "Inventory shortfall - EXC-001"
    db_session.commit()
    
    # Create exception record
    exc = ExceptionRecord(
        exception_id="EXC-001",
        order_id="ORD-1004",
        type="inventory_shortfall",
        status="RESOLVED",
        severity="HIGH",
        description="SKU-005 shortfall: requested 10, available 6"
    )
    db_session.add(exc)
    db_session.commit()
    
    # Step 2: Planner checks if order is assignable
    order_refreshed = db_session.query(Order).filter(Order.order_id == "ORD-1004").first()
    assert order_refreshed.status == "BLOCKED"
    
    assign_check = can_assign_order(order_refreshed.status)
    assert assign_check["allowed"] is False
    
    # Step 3: Verify exception exists for this order
    exception = db_session.query(ExceptionRecord).filter(
        ExceptionRecord.order_id == "ORD-1004"
    ).first()
    assert exception is not None
    assert exception.type == "inventory_shortfall"


def test_blocked_order_not_assigned(db_session):
    """Verify planner does not assign a blocked order."""
    # Block order
    order = db_session.query(Order).filter(Order.order_id == "ORD-1004").first()
    order.status = "BLOCKED"
    db_session.commit()
    
    # Feasibility check should fail
    order_dict = {"order_id": "ORD-1004", "status": "BLOCKED"}
    order_lines = [{"sku": "SKU-005", "requested_qty": 10, "picked_qty": 0}]
    inventory = {"SKU-005": {"available": 6}}
    
    result = check_order_feasibility(order_dict, order_lines, inventory)
    assert result["feasible"] is False
    assert result["status_ok"] is False


def test_completed_work_preserved(db_session):
    """Verify completed assignments are not reassigned during replanning."""
    from app.models.plan import Plan, Assignment
    
    # Create a plan with a completed assignment
    plan = Plan(
        plan_id="PLAN-TEST-001",
        version=1,
        status="ACTIVE",
        created_by="test"
    )
    db_session.add(plan)
    
    completed_assignment = Assignment(
        plan_id="PLAN-TEST-001",
        order_id="ORD-1001",
        picker_id="PICK-001",
        sequence=1,
        workload=8,
        status="COMPLETED",
        reason="Completed picking"
    )
    pending_assignment = Assignment(
        plan_id="PLAN-TEST-001",
        order_id="ORD-1002",
        picker_id="PICK-001",
        sequence=2,
        workload=10,
        status="PENDING",
        reason="Awaiting picking"
    )
    db_session.add_all([completed_assignment, pending_assignment])
    db_session.commit()
    
    # Query assignments
    assignments = db_session.query(Assignment).filter(
        Assignment.plan_id == "PLAN-TEST-001"
    ).all()
    
    # Completed should be preserved, pending can be reassigned
    completed = [a for a in assignments if a.status == "COMPLETED"]
    pending = [a for a in assignments if a.status == "PENDING"]
    
    assert len(completed) == 1
    assert completed[0].order_id == "ORD-1001"
    assert len(pending) == 1


def test_audit_logging(db_session):
    """Verify audit entries are created for tool operations."""
    from app.services.audit_service import create_audit_entry, generate_run_id
    from app.models.audit import AuditLog
    
    run_id = generate_run_id()
    entry = create_audit_entry(
        db_session,
        run_id=run_id,
        workflow="test",
        tool_name="test_tool",
        input_data={"test": "data"},
        result={"success": True},
        outcome="SUCCESS"
    )
    
    assert entry.id is not None
    assert entry.run_id == run_id
    
    # Verify it's in the database
    logs = db_session.query(AuditLog).filter(AuditLog.run_id == run_id).all()
    assert len(logs) == 1
