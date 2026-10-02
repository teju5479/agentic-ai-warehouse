"""Agent state definitions for LangGraph workflows.

These TypedDict classes define the state that flows through
the LangGraph nodes for both the Exception Resolver and Shift Planner.
"""
from typing import TypedDict, Optional, Literal, Any
from datetime import datetime


class ExceptionResolverState(TypedDict, total=False):
    """State for the Exception Resolver LangGraph workflow."""
    # Input
    exception_id: str
    run_id: str
    
    # Investigation data
    exception_data: dict
    order_data: dict
    order_lines: list[dict]
    inventory_data: dict
    shipment_data: dict
    duplicate_data: dict
    
    # Policy
    applicable_policies: list[dict]
    
    # Analysis
    evidence: list[str]
    conflicts: list[str]
    
    # Decision
    decision: str  # AUTONOMOUS, CONFIRMATION_REQUIRED, ESCALATE
    decision_reason: str
    policy_reference: str
    proposed_action: str
    effect: str
    escalation_data: dict
    
    # Result
    resolution: str
    approval_state: str  # WAITING_FOR_APPROVAL, APPROVED, REJECTED
    outcome: str  # SUCCESS, FAILURE, ESCALATED, WAITING
    
    # Errors
    errors: list[str]
    
    # LLM messages
    messages: list[Any]


class ShiftPlannerState(TypedDict, total=False):
    """State for the Shift Planner LangGraph workflow."""
    # Input
    run_id: str
    replan: bool
    original_plan_id: str
    change_reason: str
    change_type: str
    change_details: dict
    
    # Current state
    pending_orders: list[dict]
    order_lines_map: dict  # order_id -> [lines]
    inventory_map: dict  # sku -> inventory
    available_pickers: list[dict]
    existing_assignments: list[dict]
    exceptions: list[dict]
    
    # Feasibility
    feasibility_results: dict  # order_id -> feasibility check
    blocked_orders: list[dict]
    feasible_orders: list[dict]
    infeasible_orders: list[dict]
    
    # Prioritization
    prioritized_orders: list[dict]
    
    # Plan
    assignments: list[dict]
    plan_id: str
    plan_version: int
    
    # Replan specifics
    preserved_assignments: list[dict]
    changed_assignments: list[dict]
    
    # Explanation
    rationale: list[str]
    
    # Result
    outcome: str  # SUCCESS, PARTIAL, FAILURE
    
    # Errors
    errors: list[str]
    
    # LLM messages
    messages: list[Any]
