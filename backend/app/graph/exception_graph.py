import os
import json
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

# Import DB and models
from app.models.database import SessionLocal
from app.models.exception import ExceptionRecord

# Import Tools
from app.tools.exception_tools import (
    get_exception_record,
    update_exception,
    create_escalation,
    request_approval,
    approve_action,
    reject_action
)
from app.tools.order_tools import (
    get_order,
    get_order_lines,
    update_order_status,
    find_duplicate_orders
)
from app.tools.inventory_tools import check_order_inventory
from app.tools.shipment_tools import get_shipment, check_shipment_order_consistency
from app.tools.policy_tools import search_policies

# Import Audit
from app.services.audit_service import create_audit_entry, generate_run_id

# Import Rules
from app.core.rules import determine_decision_type

# Import LLM
from langchain_core.messages import HumanMessage
try:
    from app.agents.llm_provider import get_llm
except ImportError:
    def get_llm():
        return None

class ExceptionResolverState(TypedDict, total=False):
    exception_id: str
    run_id: str
    exception_data: dict
    order_data: dict
    order_lines: dict
    inventory_data: dict
    shipment_data: dict
    duplicate_data: dict
    applicable_policies: list
    evidence: dict
    conflicts: list
    decision: str
    decision_reason: str
    policy_reference: str
    proposed_action: str
    effect: str
    escalation_data: dict
    resolution: str
    approval_state: str
    outcome: str
    errors: list
    messages: list

def load_exception(state: ExceptionResolverState) -> ExceptionResolverState:
    db = SessionLocal()
    errors = state.get("errors", [])
    try:
        exc_id = state["exception_id"]
        run_id = state.get("run_id", generate_run_id())
        result = get_exception_record(db, exc_id, run_id=run_id, workflow="exception_resolver")
        
        if result.get("success"):
            exc = result["exception"]
            return {
                "run_id": run_id,
                "exception_data": exc,
                "outcome": "LOADED"
            }
        else:
            errors.append(f"Failed to load exception: {result.get('error')}")
            return {"run_id": run_id, "errors": errors, "outcome": "FAILED"}
    except Exception as e:
        errors.append(str(e))
        return {"errors": errors, "outcome": "FAILED"}
    finally:
        db.close()

def investigate(state: ExceptionResolverState) -> ExceptionResolverState:
    db = SessionLocal()
    updates = {"evidence": {}}
    errors = state.get("errors", [])
    try:
        exc_data = state.get("exception_data", {})
        order_id = exc_data.get("order_id")
        exc_type = exc_data.get("type", "")
        run_id = state.get("run_id", "")
        
        if order_id:
            # Basic order info
            updates["order_data"] = get_order(db, order_id, run_id, "exception_resolver")
            updates["order_lines"] = get_order_lines(db, order_id, run_id, "exception_resolver")
            
            # Specific tool calls based on type
            if exc_type == "inventory_shortfall":
                updates["inventory_data"] = check_order_inventory(db, order_id, run_id, "exception_resolver")
                updates["applicable_policies"] = search_policies(db, query="inventory shortfall backorder", run_id=run_id, workflow="exception_resolver")
            elif exc_type == "invalid_quantity":
                updates["applicable_policies"] = search_policies(db, query="quantity validation", run_id=run_id, workflow="exception_resolver")
            elif exc_type == "duplicate_order":
                updates["duplicate_data"] = find_duplicate_orders(db, order_id, run_id, "exception_resolver")
                updates["applicable_policies"] = search_policies(db, query="duplicate order handling", run_id=run_id, workflow="exception_resolver")
            elif exc_type == "status_conflict":
                updates["shipment_data"] = get_shipment(db, order_id, run_id, "exception_resolver")
                updates["evidence"] = check_shipment_order_consistency(db, order_id, run_id, "exception_resolver")
                updates["applicable_policies"] = search_policies(db, query="conflicting records escalation", run_id=run_id, workflow="exception_resolver")
            elif exc_type == "stale_shipment":
                updates["shipment_data"] = get_shipment(db, order_id, run_id, "exception_resolver")
                updates["applicable_policies"] = search_policies(db, query="shipment delay stale", run_id=run_id, workflow="exception_resolver")
            elif exc_type == "conflicting_destination":
                updates["shipment_data"] = get_shipment(db, order_id, run_id, "exception_resolver")
                consistency = check_shipment_order_consistency(db, order_id, run_id, "exception_resolver")
                updates["conflicts"] = consistency.get("conflicts", []) if isinstance(consistency, dict) else []
                updates["applicable_policies"] = search_policies(db, query="conflicting destination escalation", run_id=run_id, workflow="exception_resolver")
            elif exc_type == "missing_inventory":
                updates["inventory_data"] = check_order_inventory(db, order_id, run_id, "exception_resolver")
                updates["applicable_policies"] = search_policies(db, query="missing inventory escalation", run_id=run_id, workflow="exception_resolver")
            else:
                updates["applicable_policies"] = search_policies(db, query=exc_type, run_id=run_id, workflow="exception_resolver")
    except Exception as e:
        errors.append(f"Investigate error: {str(e)}")
        updates["errors"] = errors
    finally:
        db.close()
    return updates

def analyze_evidence(state: ExceptionResolverState) -> ExceptionResolverState:
    errors = state.get("errors", [])
    try:
        exc_data = state.get("exception_data", {})
        exc_type = exc_data.get("type", "")
        evidence = state.get("evidence", {})

        # Deterministic business rules are the safety authority. The LLM may
        # provide explanatory context, but it cannot override the required
        # autonomous/confirmation/escalation boundary.
        rule_decision = determine_decision_type(exc_type, evidence)
        decision = rule_decision.get("decision_type", "ESCALATE")
        reason = rule_decision.get("reason", "Unknown")
        policy = rule_decision.get("policy", "Unknown")

        try:
            llm = get_llm()
            if llm:
                prompt = (
                    f"Explain this {exc_type} exception using the supplied evidence "
                    f"{json.dumps(evidence)}. The deterministic decision is {decision}. "
                    "Do not change that decision. Return JSON with keys reason and policy."
                )
                response = llm.invoke([HumanMessage(content=prompt)])
                llm_data = json.loads(response.content)
                reason = llm_data.get("reason", reason) or reason
                policy = llm_data.get("policy", policy) or policy
        except Exception as e:
            errors.append(f"LLM advisory error: {str(e)}")

        proposed_action = ""
        if decision == "AUTONOMOUS":
            proposed_action = f"Auto-resolve {exc_type}"
        elif decision in ("CONFIRMATION", "CONFIRMATION_REQUIRED"):
            proposed_action = f"Request confirmation for {exc_type}"
        else:
            proposed_action = f"Escalate {exc_type}"

        return {
            "decision": decision,
            "decision_reason": reason,
            "policy_reference": policy,
            "proposed_action": proposed_action,
            "errors": errors
        }
    except Exception as e:
        errors.append(f"Analyze error: {str(e)}")
        return {"decision": "ESCALATE", "errors": errors}

def route_decision(state: ExceptionResolverState) -> str:
    decision = state.get("decision", "ESCALATE")
    if decision == "AUTONOMOUS":
        return "execute_autonomous"
    elif decision in ("CONFIRMATION", "CONFIRMATION_REQUIRED"):
        return "request_confirmation"
    else:
        return "create_escalation_record"

def execute_autonomous(state: ExceptionResolverState) -> ExceptionResolverState:
    db = SessionLocal()
    errors = state.get("errors", [])
    try:
        exc_data = state.get("exception_data", {})
        exc_id = exc_data.get("exception_id")
        order_id = exc_data.get("order_id")
        exc_type = exc_data.get("type", "")
        run_id = state.get("run_id", "")

        action_result = None
        if exc_type == "inventory_shortfall":
            action_result = update_order_status(
                db, order_id, "BLOCKED", "Inventory shortfall detected", run_id, "exception_resolver"
            )
            if not action_result.get("success"):
                raise RuntimeError(action_result.get("error", "Failed to block order"))
            exception_result = update_exception(
                db, exc_id, "RESOLVED", "Blocked order due to inventory shortfall",
                state.get("evidence"), state.get("policy_reference"), run_id, "exception_resolver"
            )
        elif exc_type == "invalid_quantity":
            exception_result = update_exception(
                db, exc_id, "RESOLVED", "Invalid quantity addressed",
                state.get("evidence"), state.get("policy_reference"), run_id, "exception_resolver"
            )
        elif exc_type == "stale_shipment":
            exception_result = update_exception(
                db, exc_id, "RESOLVED", "Stale shipment verified",
                state.get("evidence"), state.get("policy_reference"), run_id, "exception_resolver"
            )
        else:
            exception_result = update_exception(
                db, exc_id, "RESOLVED", f"Resolved {exc_type}",
                state.get("evidence"), state.get("policy_reference"), run_id, "exception_resolver"
            )

        if not exception_result.get("success"):
            raise RuntimeError(exception_result.get("error", "Failed to update exception"))

        create_audit_entry(
            db=db,
            run_id=run_id,
            workflow="exception_resolver",
            tool_name="execute_autonomous",
            input_data={"exception_id": exc_id, "type": exc_type},
            result={"action_result": action_result, "exception_result": exception_result},
            policy_reference=state.get("policy_reference"),
            decision="AUTONOMOUS",
            proposed_action=state.get("proposed_action"),
            state_changes={"order_id": order_id, "confirmed_by_tool": True},
            outcome="SUCCESS"
        )
        return {"outcome": "RESOLVED", "resolution": f"Auto-resolved {exc_type}"}
    except Exception as e:
        errors.append(f"Execute error: {str(e)}")
        if run_id:
            create_audit_entry(
                db=db, run_id=run_id, workflow="exception_resolver",
                tool_name="execute_autonomous", input_data={"exception_id": exc_data.get("exception_id") if 'exc_data' in locals() else None},
                error=str(e), policy_reference=state.get("policy_reference"),
                decision="AUTONOMOUS", proposed_action=state.get("proposed_action"), outcome="FAILURE"
            )
        return {"errors": errors, "outcome": "FAILED"}
    finally:
        db.close()

def request_confirmation(state: ExceptionResolverState) -> ExceptionResolverState:
    db = SessionLocal()
    errors = state.get("errors", [])
    try:
        exc_data = state.get("exception_data", {})
        exc_id = exc_data.get("exception_id")
        exc_type = exc_data.get("type", "")
        run_id = state.get("run_id", "")

        if exc_type == "duplicate_order":
            action = f"Hold duplicate order {exc_data.get('order_id')}"
            action_type = "hold_order"
        else:
            action = state.get("proposed_action") or f"Proposed action for {exc_type}"
            action_type = ""
        reason = state.get("decision_reason") or f"Confirmation required for {exc_type}"
        policy = state.get("policy_reference") or "SOP-003"
        effect = state.get("effect") or "Consequential state modification requires human approval"

        request_approval(
            db, exc_id, action=action, reason=reason, policy=policy, effect=effect,
            action_type=action_type, run_id=run_id, workflow="exception_resolver"
        )

        return {"outcome": "PENDING_APPROVAL", "approval_state": "REQUESTED"}
    except Exception as e:
        errors.append(f"Request confirmation error: {str(e)}")
        return {"errors": errors, "outcome": "FAILED"}
    finally:
        db.close()

def create_escalation_record(state: ExceptionResolverState) -> ExceptionResolverState:
    db = SessionLocal()
    errors = state.get("errors", [])
    try:
        exc_data = state.get("exception_data", {})
        exc_id = exc_data.get("exception_id")
        run_id = state.get("run_id", "")
        
        evidence = state.get("evidence", {})
        evidence_list = []
        for k, v in evidence.items():
            if v:
                evidence_list.append(k)
        
        create_escalation(
            db=db,
            exception_id=exc_id,
            issue=f"Requires escalation: {exc_data.get('type')}",
            evidence_checked=evidence_list,
            conflicts=state.get("conflicts", []),
            policy_reference=state.get("policy_reference", ""),
            recommended_action=state.get("proposed_action", ""),
            unresolved_questions=["Manual review required"],
            run_id=run_id,
            workflow="exception_resolver"
        )
        return {"outcome": "ESCALATED"}
    except Exception as e:
        errors.append(f"Escalation error: {str(e)}")
        return {"errors": errors, "outcome": "FAILED"}
    finally:
        db.close()

def get_graph():
    builder = StateGraph(ExceptionResolverState)
    builder.add_node("load_exception", load_exception)
    builder.add_node("investigate", investigate)
    builder.add_node("analyze_evidence", analyze_evidence)
    builder.add_node("execute_autonomous", execute_autonomous)
    builder.add_node("request_confirmation", request_confirmation)
    builder.add_node("create_escalation_record", create_escalation_record)
    
    builder.set_entry_point("load_exception")
    builder.add_edge("load_exception", "investigate")
    builder.add_edge("investigate", "analyze_evidence")
    builder.add_conditional_edges("analyze_evidence", route_decision, {
        "execute_autonomous": "execute_autonomous",
        "request_confirmation": "request_confirmation",
        "create_escalation_record": "create_escalation_record"
    })
    
    builder.add_edge("execute_autonomous", END)
    builder.add_edge("request_confirmation", END)
    builder.add_edge("create_escalation_record", END)
    
    return builder.compile()

def run_exception_resolver(exception_id: str) -> dict:
    graph = get_graph()
    run_id = generate_run_id()
    initial_state = {"exception_id": exception_id, "run_id": run_id}
    result = graph.invoke(initial_state)
    return result

def approve_exception_action(exception_id: str) -> dict:
    db = SessionLocal()
    try:
        run_id = generate_run_id()
        result = approve_action(db, exception_id, run_id=run_id, workflow="exception_resolver")
        return result
    finally:
        db.close()

def reject_exception_action(exception_id: str, reason: str = "") -> dict:
    db = SessionLocal()
    try:
        run_id = generate_run_id()
        result = reject_action(db, exception_id, reason=reason, run_id=run_id, workflow="exception_resolver")
        return result
    finally:
        db.close()
