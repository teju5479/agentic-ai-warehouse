"""Exception management tools for agent workflows."""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.exception import ExceptionRecord
from app.models.order import Order
from app.services.audit_service import create_audit_entry
from app.tools.order_tools import hold_order


def create_exception_record(
    db: Session,
    order_id: str,
    exc_type: str,
    severity: str,
    description: str,
    run_id: str = "",
    workflow: str = "",
) -> dict:
    """Create new exception with auto-ID."""
    exc_id = f"EXC-{uuid.uuid4().hex[:8].upper()}"

    try:
        new_exc = ExceptionRecord(
            exception_id=exc_id,
            order_id=order_id,
            type=exc_type,
            severity=severity,
            description=description,
            status="OPEN",
        )

        db.add(new_exc)
        db.commit()

        result = {
            "success": True,
            "exception_id": exc_id,
            "status": "OPEN",
        }

        if run_id:
            create_audit_entry(
                db,
                run_id,
                workflow,
                "create_exception_record",
                {
                    "order_id": order_id,
                    "type": exc_type,
                    "severity": severity,
                },
                result=result,
                outcome="SUCCESS",
            )

        return result

    except Exception as e:
        db.rollback()

        if run_id:
            create_audit_entry(
                db,
                run_id,
                workflow,
                "create_exception_record",
                {"order_id": order_id},
                error=str(e),
                outcome="FAILURE",
            )

        return {
            "success": False,
            "error": str(e),
        }


def update_exception(
    db: Session,
    exception_id: str,
    status: str,
    resolution: str = None,
    evidence: dict = None,
    policy_reference: str = None,
    run_id: str = "",
    workflow: str = "",
) -> dict:
    """Update exception with validation."""

    exc = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.exception_id == exception_id)
        .first()
    )

    if not exc:
        return {
            "success": False,
            "error": f"Exception {exception_id} not found",
        }

    valid_statuses = [
        "OPEN",
        "ESCALATED",
        "WAITING_FOR_APPROVAL",
        "RESOLVED",
        "REJECTED",
    ]

    if status not in valid_statuses:
        return {
            "success": False,
            "error": f"Invalid status {status}",
        }

    old_status = exc.status
    exc.status = status

    if resolution:
        exc.resolution = resolution

    if evidence:
        exc.evidence = json.dumps(evidence) if evidence else None

    if policy_reference:
        exc.policy_reference = policy_reference

    db.commit()

    result = {
        "success": True,
        "exception_id": exception_id,
        "old_status": old_status,
        "new_status": status,
    }

    if run_id:
        create_audit_entry(
            db,
            run_id,
            workflow,
            "update_exception",
            {
                "exception_id": exception_id,
                "status": status,
            },
            state_changes={
                "exception": exception_id,
                "old_status": old_status,
                "new_status": status,
            },
            outcome="SUCCESS",
        )

    return result


def get_exception_record(
    db: Session,
    exception_id: str,
    run_id: str = "",
    workflow: str = "",
) -> dict:
    """Get exception details."""

    exc = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.exception_id == exception_id)
        .first()
    )

    if not exc:
        return {
            "success": False,
            "error": f"Exception {exception_id} not found",
        }

    result = {
        "success": True,
        "exception": {
            "exception_id": exc.exception_id,
            "order_id": exc.order_id,
            "type": exc.type,
            "severity": exc.severity,
            "description": exc.description,
            "status": exc.status,
            "resolution": exc.resolution,
            "evidence": exc.evidence,
            "policy_reference": exc.policy_reference,
            "proposed_action": exc.proposed_action,
        },
    }

    if run_id:
        create_audit_entry(
            db,
            run_id,
            workflow,
            "get_exception_record",
            {"exception_id": exception_id},
            outcome="SUCCESS",
        )

    return result


def create_escalation(
    db: Session,
    exception_id: str,
    issue: str,
    evidence_checked: list,
    conflicts: list,
    policy_reference: str,
    recommended_action: str,
    unresolved_questions: list,
    run_id: str = "",
    workflow: str = "",
) -> dict:
    """Create structured escalation, updates exception status to ESCALATED."""

    exc = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.exception_id == exception_id)
        .first()
    )

    if not exc:
        return {
            "success": False,
            "error": f"Exception {exception_id} not found",
        }

    escalation_data = {
        "issue": issue,
        "evidence_checked": evidence_checked,
        "conflicts": conflicts,
        "unresolved_questions": unresolved_questions,
        "recommended_action": recommended_action,
    }

    old_status = exc.status
    exc.status = "ESCALATED"
    exc.evidence = json.dumps(escalation_data)
    exc.policy_reference = policy_reference

    db.commit()

    result = {
        "success": True,
        "exception_id": exception_id,
        "new_status": "ESCALATED",
    }

    if run_id:
        create_audit_entry(
            db,
            run_id,
            workflow,
            "create_escalation",
            {"exception_id": exception_id},
            state_changes={
                "exception": exception_id,
                "old_status": old_status,
                "new_status": "ESCALATED",
            },
            outcome="SUCCESS",
        )

    return result


def request_approval(
    db: Session,
    exception_id: str,
    action: str,
    reason: str,
    policy: str,
    effect: str,
    action_type: str = "",
    run_id: str = "",
    workflow: str = "",
) -> dict:
    """Set exception status to WAITING_FOR_APPROVAL and store proposed action details."""

    exc = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.exception_id == exception_id)
        .first()
    )

    if not exc:
        return {
            "success": False,
            "error": f"Exception {exception_id} not found",
        }

    proposed = {
        "action": action,
        "reason": reason,
        "policy": policy,
        "effect": effect,
        "action_type": action_type,
    }

    old_status = exc.status
    exc.status = "WAITING_FOR_APPROVAL"
    exc.proposed_action = json.dumps(proposed)

    db.commit()

    result = {
        "success": True,
        "exception_id": exception_id,
        "new_status": "WAITING_FOR_APPROVAL",
    }

    if run_id:
        create_audit_entry(
            db,
            run_id,
            workflow,
            "request_approval",
            {
                "exception_id": exception_id,
                "action": action,
            },
            state_changes={
                "exception": exception_id,
                "old_status": old_status,
                "new_status": "WAITING_FOR_APPROVAL",
            },
            proposed_action=action,
            approval_state="REQUESTED",
            policy_reference=policy,
            outcome="SUCCESS",
        )

    return result


def approve_action(
    db: Session,
    exception_id: str,
    run_id: str = "",
    workflow: str = "",
) -> dict:
    """Execute the approved action (reads proposed action from exception)."""

    exc = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.exception_id == exception_id)
        .first()
    )

    if not exc:
        return {
            "success": False,
            "error": f"Exception {exception_id} not found",
        }

    if exc.status != "WAITING_FOR_APPROVAL":
        return {
            "success": False,
            "error": (
                f"Exception {exception_id} is not waiting for approval "
                f"(current status: {exc.status})"
            ),
        }

    if not exc.proposed_action:
        return {
            "success": False,
            "error": f"No proposed action found for exception {exception_id}",
        }

    try:
        action_details = (
            json.loads(exc.proposed_action)
            if isinstance(exc.proposed_action, str)
            else exc.proposed_action
        )
    except (json.JSONDecodeError, TypeError):
        action_details = {
            "action": str(exc.proposed_action)
        }

    old_status = exc.status
    action_type = action_details.get("action_type", "")
    action_text = action_details.get("action", "")
    action_result = None

    # Execute only explicitly supported, policy-gated actions.
    if action_type == "hold_order":

        order = (
            db.query(Order)
            .filter(Order.order_id == exc.order_id)
            .first()
        )

        if not order:
            return {
                "success": False,
                "exception_id": exception_id,
                "error": f"Order {exc.order_id} not found",
            }

        # Idempotent approval:
        # If the order is already HELD, the requested action is
        # already satisfied. Do not attempt HELD -> HELD.
        if order.status == "HELD":

            action_result = {
                "success": True,
                "order_id": exc.order_id,
                "old_status": "HELD",
                "new_status": "HELD",
                "reason": order.held_reason,
                "already_applied": True,
                "message": (
                    "Order is already HELD; "
                    "approved action is already satisfied."
                ),
            }

        else:

            action_result = hold_order(
                db,
                exc.order_id,
                action_details.get(
                    "reason",
                    "Approved duplicate-order hold",
                ),
                run_id,
                workflow,
            )

            if not action_result.get("success"):
                return {
                    "success": False,
                    "exception_id": exception_id,
                    "error": action_result.get(
                        "error",
                        "Approved action execution failed",
                    ),
                }

    else:
        return {
            "success": False,
            "exception_id": exception_id,
            "error": (
                "Unsupported approved action type: "
                f"{action_type or action_text}"
            ),
        }

    # Resolve the exception only after the approved action has
    # been successfully executed or confirmed as already applied.
    exc.status = "RESOLVED"
    exc.resolution = (
        f"Approved action executed successfully: {action_text}"
    )
    exc.resolved_at = datetime.utcnow()

    db.commit()

    result = {
        "success": True,
        "exception_id": exception_id,
        "executed_action": action_text,
        "action_result": action_result,
        "new_status": "RESOLVED",
    }

    if run_id:
        create_audit_entry(
            db,
            run_id,
            workflow,
            "approve_action",
            {
                "exception_id": exception_id,
                "action_type": action_type,
            },
            result=result,
            state_changes={
                "exception": exception_id,
                "old_status": old_status,
                "new_status": "RESOLVED",
                "controlled_action_executed": True,
                "order_id": exc.order_id,
            },
            approval_state="APPROVED",
            outcome="SUCCESS",
        )

    return result


def reject_action(
    db: Session,
    exception_id: str,
    reason: str,
    run_id: str = "",
    workflow: str = "",
) -> dict:
    """Reject the proposed action."""

    exc = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.exception_id == exception_id)
        .first()
    )

    if not exc:
        return {
            "success": False,
            "error": f"Exception {exception_id} not found",
        }

    if exc.status != "WAITING_FOR_APPROVAL":
        return {
            "success": False,
            "error": (
                f"Exception {exception_id} is not waiting for approval"
            ),
        }

    old_status = exc.status
    exc.status = "REJECTED"
    exc.resolution = f"Rejected: {reason}"

    db.commit()

    result = {
        "success": True,
        "exception_id": exception_id,
        "new_status": "REJECTED",
    }

    if run_id:
        create_audit_entry(
            db,
            run_id,
            workflow,
            "reject_action",
            {
                "exception_id": exception_id,
                "reason": reason,
            },
            state_changes={
                "exception": exception_id,
                "old_status": old_status,
                "new_status": "REJECTED",
            },
            outcome="SUCCESS",
        )

    return result