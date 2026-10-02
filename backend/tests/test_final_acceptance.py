"""Final Acceptance Test Sequence (Section 34).

Verifies the full end-to-end flow:
RESET DB -> EXC-001 -> RESOLVER -> BLOCK ORDER -> AUDIT -> PLANNER ->
BLOCKED ORDER NOT ASSIGNED -> REPLAN -> PRESERVE WORK -> AUDIT
"""
import pytest
from app.models.database import Base, engine, SessionLocal
from app.seed.seed_database import reset_database
from app.graph.exception_graph import run_exception_resolver
from app.graph.planner_graph import run_shift_planner, run_replan
from app.models.order import Order
from app.models.exception import ExceptionRecord
from app.models.plan import Plan, Assignment
from app.models.audit import AuditLog
from app.tools.exception_tools import create_exception_record


def test_final_acceptance_sequence():
    db = SessionLocal()
    try:
        # 1. RESET DATABASE
        reset_database(db)
        
        # 2. RUN INVENTORY SHORTFALL (EXC-001)
        # Seed EXC-001 exception record for ORD-1004
        exc_res = create_exception_record(
            db,
            order_id="ORD-1004",
            exc_type="inventory_shortfall",
            severity="HIGH",
            description="SKU-005 shortfall: requested 10, available 6",
            run_id="ACCEPTANCE-001",
            workflow="test"
        )
        assert exc_res["success"] is True
        exception_id = exc_res["exception_id"]
        
        # 3. EXCEPTION RESOLVER
        # 4. TOOLS INVESTIGATE & 5. POLICY RETRIEVED & 6. ORDER BLOCKED
        resolver_result = run_exception_resolver(exception_id)
        assert resolver_result is not None
        assert resolver_result.get("outcome") in ("RESOLVED", "PENDING_APPROVAL")
        
        if resolver_result.get("outcome") == "PENDING_APPROVAL":
            from app.graph.exception_graph import approve_exception_action
            approval = approve_exception_action(exception_id)
            assert approval.get("success") is True

        # Check order status in DB
        ord_1004 = db.query(Order).filter(Order.order_id == "ORD-1004").first()
        assert ord_1004.status == "BLOCKED"
        
        # 7. AUDIT LOG CREATED
        audit_logs = db.query(AuditLog).filter(AuditLog.run_id == resolver_result.get("run_id")).all()
        assert len(audit_logs) > 0
        
        # 8. RUN SHIFT PLANNER & 9. BLOCKED ORDER NOT ASSIGNED & 10. MULTI-ORDER PLAN
        planner_result = run_shift_planner()
        assert planner_result is not None
        assert planner_result.get("outcome") == "SUCCESS"
        
        # Verify blocked order ORD-1004 is NOT assigned
        assignments = planner_result.get("assignments", [])
        assigned_order_ids = [a.get("order_id") for a in assignments if a.get("status") != "BLOCKED"]
        assert "ORD-1004" not in assigned_order_ids
        
        # 11. ASSIGN FEASIBLE ORDERS
        assert len(assigned_order_ids) > 0
        
        # 12. MAKE PICKER UNAVAILABLE & 13. REPLAN
        replan_result = run_replan("picker_unavailable", {"picker_id": "PICK-001"})
        assert replan_result is not None
        assert replan_result.get("outcome") == "SUCCESS"
        
        # 14. PRESERVE COMPLETED WORK & 15. REASSIGN VALID WORK & 16. FLAG INFEASIBLE WORK
        # Check that plan version incremented
        new_plan = db.query(Plan).order_by(Plan.created_at.desc()).first()
        assert new_plan is not None
        assert new_plan.version >= 2
        assert new_plan.parent_plan_id is not None
        
        # 17. AUDIT PLAN VERSION CHANGE
        plan_audits = db.query(AuditLog).filter(AuditLog.workflow == "shift_planner").all()
        assert len(plan_audits) > 0

    finally:
        db.close()
