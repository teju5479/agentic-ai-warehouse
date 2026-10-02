import uuid
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.exception import ExceptionRecord
from app.models.order import Order
from app.tools.order_tools import get_pending_orders, get_order_lines
from app.tools.inventory_tools import get_all_inventory
from app.tools.picker_tools import get_available_pickers, update_picker_availability
from app.tools.planning_tools import create_plan, get_current_plan
from app.core.feasibility import (
    check_order_feasibility,
    calculate_workload,
    check_picker_capacity,
    validate_assignment
)
from app.core.prioritization import prioritize_orders
from app.services.audit_service import create_audit_entry, generate_run_id

logger = logging.getLogger(__name__)

def generate_run_id() -> str:
    return str(uuid.uuid4())

class PlannerState(TypedDict):
    run_id: str
    replan: bool
    change_type: Optional[str]
    change_details: Optional[Dict[str, Any]]
    
    # Raw Data
    pending_orders: List[Dict[str, Any]]
    order_lines_map: Dict[str, List[Dict[str, Any]]]
    inventory_map: Dict[str, Dict[str, Any]]
    available_pickers: List[Dict[str, Any]]
    
    # Replanning state
    existing_assignments: List[Dict[str, Any]]
    existing_plan_id: Optional[str]
    existing_plan_version: int
    preserved_assignments: List[Dict[str, Any]]
    affected_assignments: List[Dict[str, Any]]
    unchanged_assignments: List[Dict[str, Any]]
    
    # Processed Data
    feasible_orders: List[Dict[str, Any]]
    blocked_orders: List[Dict[str, Any]]
    infeasible_orders: List[Dict[str, Any]]
    prioritized_orders: List[Dict[str, Any]]
    
    # Output
    draft_assignments: List[Dict[str, Any]]
    final_assignments: List[Dict[str, Any]]
    assignments: List[Dict[str, Any]]
    plan_id: Optional[str]
    outcome: Optional[str]
    
    errors: List[str]
    rationale: List[str]

def load_warehouse_state(state: PlannerState) -> PlannerState:
    """Load the current state of the warehouse from the database."""
    logger.info("Loading warehouse state")
    db: Session = SessionLocal()
    run_id = state.get("run_id", "")
    workflow = "shift_planner"
    try:
        orders_result = get_pending_orders(db, run_id, workflow)
        pending_orders = orders_result.get("orders", [])
        
        order_lines_map = {}
        for order in pending_orders:
            order_id = order.get("order_id")
            if order_id:
                lines_result = get_order_lines(db, order_id, run_id, workflow)
                order_lines_map[order_id] = lines_result.get("order_lines", [])
                
        inventory_result = get_all_inventory(db, run_id, workflow)
        inventory_list = inventory_result.get("inventory", [])
        inventory_map = {item.get("sku"): item for item in inventory_list if item.get("sku")}
        
        pickers_result = get_available_pickers(db, run_id, workflow)
        available_pickers = pickers_result.get("pickers", [])
        
        # Check exceptions
        open_exceptions = db.query(ExceptionRecord).filter(ExceptionRecord.status == "OPEN").all()
        exception_order_ids = set(exc.order_id for exc in open_exceptions if exc.order_id)
        
        for order in pending_orders:
            order["has_open_exception"] = order.get("order_id") in exception_order_ids
            
        return {
            **state,
            "pending_orders": pending_orders,
            "order_lines_map": order_lines_map,
            "inventory_map": inventory_map,
            "available_pickers": available_pickers,
            "rationale": state.get("rationale", []) + ["Loaded warehouse state"]
        }
    except Exception as e:
        logger.error(f"Error loading warehouse state: {e}")
        return {**state, "errors": state.get("errors", []) + [f"Failed to load state: {str(e)}"]}
    finally:
        db.close()

def load_existing_plan(state: PlannerState) -> PlannerState:
    """Load the current active plan for replanning."""
    if not state.get("replan"):
        return state
        
    db: Session = SessionLocal()
    run_id = state.get("run_id", "")
    workflow = "shift_planner"
    try:
        plan_result = get_current_plan(db, run_id, workflow)
        plan_data = plan_result.get("plan", {})
        existing_assignments = plan_data.get("assignments", [])
        return {
            **state,
            "existing_plan_id": plan_data.get("plan_id"),
            "existing_plan_version": plan_data.get("version", 1),
            "existing_assignments": existing_assignments,
            "rationale": state.get("rationale", []) + ["Loaded existing plan for replanning"]
        }
    except Exception as e:
        logger.error(f"Error loading existing plan: {e}")
        return {**state, "errors": state.get("errors", []) + [f"Failed to load existing plan: {str(e)}"]}
    finally:
        db.close()

def identify_affected(state: PlannerState) -> PlannerState:
    """Identify which assignments are affected by the change."""
    if not state.get("replan"):
        return state
        
    existing = state.get("existing_assignments", [])
    change_type = state.get("change_type")
    change_details = state.get("change_details", {})
    
    preserved = []
    affected = []
    unchanged = []
    
    for assign in existing:
        status = assign.get("status")
        if status in ("COMPLETED", "IN_PROGRESS"):
            preserved.append(assign)
        elif change_type == "picker_unavailable" and assign.get("picker_id") == change_details.get("picker_id") and status == "PENDING":
            affected.append(assign)
        else:
            unchanged.append(assign)
            
    return {
        **state,
        "preserved_assignments": preserved,
        "affected_assignments": affected,
        "unchanged_assignments": unchanged,
        "rationale": state.get("rationale", []) + [f"Identified affected assignments (type: {change_type})"]
    }

def check_feasibility(state: PlannerState) -> PlannerState:
    """Check which orders can be fulfilled based on inventory and exceptions."""
    pending_orders = state.get("pending_orders", [])
    order_lines_map = state.get("order_lines_map", {})
    inventory_map = state.get("inventory_map", {})
    
    feasible = []
    blocked = []
    infeasible = []
    
    # If replanning, only consider orders that aren't already preserved or unchanged
    if state.get("replan"):
        handled_order_ids = {a.get("order_id") for a in state.get("preserved_assignments", []) + state.get("unchanged_assignments", [])}
        orders_to_check = [o for o in pending_orders if o.get("order_id") not in handled_order_ids]
    else:
        orders_to_check = pending_orders

    for order in orders_to_check:
        order_id = order.get("order_id")
        lines = order_lines_map.get(order_id, [])
        
        if order.get("has_open_exception"):
            order["blocked_reason"] = "Open exception exists"
            blocked.append(order)
            continue
            
        feasibility = check_order_feasibility(order, lines, inventory_map)
        if feasibility.get("feasible"):
            feasible.append(order)
        elif not feasibility.get("inventory_ready"):
            order["blocked_reason"] = "Insufficient inventory: " + ", ".join(feasibility.get("reasons", []))
            blocked.append(order)
        else:
            order["blocked_reason"] = ", ".join(feasibility.get("reasons", []))
            infeasible.append(order)
            
    return {
        **state,
        "feasible_orders": feasible,
        "blocked_orders": blocked,
        "infeasible_orders": infeasible,
        "rationale": state.get("rationale", []) + [f"Found {len(feasible)} feasible orders"]
    }

def prioritize_orders_node(state: PlannerState) -> PlannerState:
    """Score and prioritize feasible orders."""
    feasible = state.get("feasible_orders", [])
    order_lines_map = state.get("order_lines_map", {})
    inventory_map = state.get("inventory_map", {})
    
    prioritized = prioritize_orders(feasible, order_lines_map, inventory_map)
    
    return {
        **state,
        "prioritized_orders": prioritized,
        "rationale": state.get("rationale", []) + ["Prioritized orders"]
    }

def generate_assignments(state: PlannerState) -> PlannerState:
    """Generate draft assignments mapping orders to pickers."""
    prioritized = state.get("prioritized_orders", [])
    pickers = state.get("available_pickers", [])
    order_lines_map = state.get("order_lines_map", {})
    
    # Track workloads
    picker_workloads = {p.get("picker_id"): p.get("current_workload", 0) for p in pickers}
    picker_caps = {p.get("picker_id"): p.get("capacity", 100) for p in pickers}
    
    assignments = []
    blocked_further = []
    
    # If replanning, add unchanged assignments to workload
    if state.get("replan"):
        for a in state.get("unchanged_assignments", []):
            pid = a.get("picker_id")
            if pid in picker_workloads:
                picker_workloads[pid] += a.get("workload", 0)
    
    # Sort orders by score descending
    prioritized.sort(key=lambda x: x.get("score", {}).get("total_score", 0), reverse=True)
    
    for order_data in prioritized:
        order = order_data.get("order", order_data)
        order_id = order.get("order_id")
        lines = order_lines_map.get(order_id, [])
        workload = calculate_workload(lines)
        
        # Find capable pickers
        capable = []
        for p in pickers:
            pid = p.get("picker_id")
            current = picker_workloads.get(pid, 0)
            cap = picker_caps.get(pid, 100)
            if current + workload <= cap:
                capable.append({**p, "remaining": cap - current - workload})
                
        if not capable:
            order["blocked_reason"] = "No picker with sufficient capacity"
            blocked_further.append(order)
            continue
            
        # Assign to picker with most remaining capacity
        capable.sort(key=lambda x: x["remaining"], reverse=True)
        chosen = capable[0]
        chosen_id = chosen.get("picker_id")
        
        picker_workloads[chosen_id] += workload
        
        assignments.append({
            "order_id": order_id,
            "picker_id": chosen_id,
            "sequence": len(assignments) + 1,
            "workload": workload,
            "status": "PENDING",
            "reason": "Automated assignment"
        })
        
    return {
        **state,
        "draft_assignments": assignments,
        "blocked_orders": state.get("blocked_orders", []) + blocked_further,
        "rationale": state.get("rationale", []) + [f"Generated {len(assignments)} draft assignments"]
    }

def validate_assignments_node(state: PlannerState) -> PlannerState:
    """Validate draft assignments against constraints."""
    drafts = state.get("draft_assignments", [])
    order_lines_map = state.get("order_lines_map", {})
    inventory_map = state.get("inventory_map", {})
    pickers = state.get("available_pickers", [])
    pending_orders = {o.get("order_id"): o for o in state.get("pending_orders", [])}
    
    picker_map = {p.get("picker_id"): p for p in pickers}
    
    valid_assignments = []
    invalid_assignments = []
    
    for draft in drafts:
        order_id = draft.get("order_id")
        picker_id = draft.get("picker_id")
        
        order = pending_orders.get(order_id)
        picker = picker_map.get(picker_id)
        lines = order_lines_map.get(order_id, [])
        
        if not order or not picker:
            invalid_assignments.append(draft)
            continue
            
        validation = validate_assignment(order, lines, picker, inventory_map)
        if validation.get("valid"):
            valid_assignments.append(draft)
        else:
            invalid_assignments.append(draft)
            
    return {
        **state,
        "final_assignments": valid_assignments,
        "rationale": state.get("rationale", []) + [f"Validated {len(valid_assignments)} assignments"]
    }

def create_plan_record(state: PlannerState) -> PlannerState:
    """Save the final plan and assignments to the database."""
    db: Session = SessionLocal()
    run_id = state.get("run_id", "")
    workflow = "shift_planner"
    try:
        assignments_to_save = []
        
        if state.get("replan"):
            assignments_to_save.extend(state.get("preserved_assignments", []))
            assignments_to_save.extend(state.get("unchanged_assignments", []))
            
        assignments_to_save.extend(state.get("final_assignments", []))
        
        # Add blocked orders to the plan for visibility
        for blocked in state.get("blocked_orders", []):
            assignments_to_save.append({
                "order_id": blocked.get("order_id"),
                "picker_id": "",
                "sequence": 0,
                "workload": 0,
                "status": "BLOCKED",
                "reason": blocked.get("blocked_reason", "Blocked")
            })
            
        version = 1
        parent_plan_id = ""
        supersede_plan_id = ""
        if state.get("replan"):
            parent_plan_id = state.get("existing_plan_id") or ""
            version = int(state.get("existing_plan_version", 1)) + 1
            supersede_plan_id = parent_plan_id

        result = create_plan(
            db, assignments_to_save, "shift_planner", run_id, workflow,
            version=version, parent_plan_id=parent_plan_id, supersede_plan_id=supersede_plan_id
        )
        if not result.get("success"):
            return {
                **state,
                "outcome": "FAILURE",
                "errors": state.get("errors", []) + [result.get("error", "Plan creation failed")]
            }

        return {
            **state,
            "outcome": "SUCCESS",
            "plan_id": result.get("plan_id"),
            "assignments": assignments_to_save,
            "rationale": state.get("rationale", []) + [f"Created plan {result.get('plan_id')} version {result.get('version', version)}"]
        }
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        return {**state, "outcome": "FAILURE", "errors": state.get("errors", []) + [f"Failed to create plan: {str(e)}"]}
    finally:
        db.close()


def should_replan(state: PlannerState) -> str:
    if state.get("replan"):
        return "replan"
    return "normal"


def build_planner_graph(replan: bool = False):
    workflow = StateGraph(PlannerState)
    
    workflow.add_node("load_warehouse_state", load_warehouse_state)
    workflow.add_node("check_feasibility", check_feasibility)
    workflow.add_node("prioritize_orders_node", prioritize_orders_node)
    workflow.add_node("generate_assignments", generate_assignments)
    workflow.add_node("validate_assignments_node", validate_assignments_node)
    workflow.add_node("create_plan_record", create_plan_record)
    
    workflow.set_entry_point("load_warehouse_state")
    
    if replan:
        workflow.add_node("load_existing_plan", load_existing_plan)
        workflow.add_node("identify_affected", identify_affected)
        
        workflow.add_edge("load_warehouse_state", "load_existing_plan")
        workflow.add_edge("load_existing_plan", "identify_affected")
        workflow.add_edge("identify_affected", "check_feasibility")
    else:
        workflow.add_edge("load_warehouse_state", "check_feasibility")
        
    workflow.add_edge("check_feasibility", "prioritize_orders_node")
    workflow.add_edge("prioritize_orders_node", "generate_assignments")
    workflow.add_edge("generate_assignments", "validate_assignments_node")
    workflow.add_edge("validate_assignments_node", "create_plan_record")
    workflow.add_edge("create_plan_record", END)
    
    return workflow.compile()


def run_shift_planner():
    """Run the shift planner. Returns result dict."""
    graph = build_planner_graph(replan=False)
    run_id = generate_run_id()
    initial_state = {"run_id": run_id, "replan": False, "errors": [], "rationale": []}
    result = graph.invoke(initial_state)
    return result

def run_replan(change_type: str, change_details: dict):
    """Run replanning after a change event."""
    db = SessionLocal()
    try:
        if change_type == "picker_unavailable":
            picker_id = change_details.get("picker_id")
            if picker_id:
                update_picker_availability(db, picker_id, "UNAVAILABLE")
    finally:
        db.close()
    
    graph = build_planner_graph(replan=True)
    run_id = generate_run_id()
    initial_state = {
        "run_id": run_id, 
        "replan": True, 
        "change_type": change_type,
        "change_details": change_details, 
        "errors": [], 
        "rationale": []
    }
    return graph.invoke(initial_state)
