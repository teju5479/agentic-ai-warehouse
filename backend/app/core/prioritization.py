"""Order prioritization engine.

Uses a transparent, configurable heuristic to rank orders.
This is NOT a globally optimal solution - it is a coherent,
explainable priority ranking.
"""
from datetime import datetime
from typing import Any
from app.core.feasibility import calculate_deadline_urgency, calculate_workload, check_inventory_readiness


# Priority weight configuration
DEFAULT_WEIGHTS = {
    "deadline_urgency": 0.35,
    "order_priority": 0.25,
    "inventory_readiness": 0.20,
    "existing_progress": 0.10,
    "workload_efficiency": 0.10,
}

PRIORITY_SCORES = {
    "URGENT": 100,
    "HIGH": 75,
    "MEDIUM": 50,
    "LOW": 25,
}


def calculate_priority_score(
    order: dict,
    order_lines: list[dict],
    inventory: dict[str, dict],
    weights: dict | None = None
) -> dict:
    """Calculate a composite priority score for an order.
    
    Returns:
        {total_score: float, breakdown: {factor: score}, rank_factors: dict}
    """
    w = weights or DEFAULT_WEIGHTS
    
    # 1. Deadline urgency
    urgency = calculate_deadline_urgency(order.get("deadline"))
    urgency_score = urgency["urgency_score"]
    
    # 2. Order priority
    priority_score = PRIORITY_SCORES.get(order.get("priority", "MEDIUM"), 50)
    
    # 3. Inventory readiness
    inv_check = check_inventory_readiness(order_lines, inventory)
    readiness_score = 100 if inv_check["ready"] else 0
    
    # 4. Existing progress (how much has already been picked)
    total_requested = sum(l["requested_qty"] for l in order_lines if l["requested_qty"] > 0)
    total_picked = sum(l.get("picked_qty", 0) for l in order_lines)
    progress_score = (total_picked / total_requested * 100) if total_requested > 0 else 0
    
    # 5. Workload efficiency (smaller = more efficient to complete)
    workload = calculate_workload(order_lines)
    efficiency_score = max(0, 100 - workload * 5)  # Penalize large workloads slightly
    
    # Composite score
    total = (
        w["deadline_urgency"] * urgency_score +
        w["order_priority"] * priority_score +
        w["inventory_readiness"] * readiness_score +
        w["existing_progress"] * progress_score +
        w["workload_efficiency"] * efficiency_score
    )
    
    return {
        "total_score": round(total, 2),
        "breakdown": {
            "deadline_urgency": round(w["deadline_urgency"] * urgency_score, 2),
            "order_priority": round(w["order_priority"] * priority_score, 2),
            "inventory_readiness": round(w["inventory_readiness"] * readiness_score, 2),
            "existing_progress": round(w["existing_progress"] * progress_score, 2),
            "workload_efficiency": round(w["workload_efficiency"] * efficiency_score, 2),
        },
        "rank_factors": {
            "urgency": urgency,
            "priority": order.get("priority"),
            "inventory_ready": inv_check["ready"],
            "progress_pct": round(progress_score, 1),
            "workload": workload,
        }
    }


def prioritize_orders(
    orders: list[dict],
    order_lines_map: dict[str, list[dict]],
    inventory: dict[str, dict],
    weights: dict | None = None
) -> list[dict]:
    """Prioritize a list of orders by composite score.
    
    Returns list sorted by priority (highest first), each with score details.
    """
    scored = []
    for order in orders:
        oid = order["order_id"]
        lines = order_lines_map.get(oid, [])
        score_info = calculate_priority_score(order, lines, inventory, weights)
        scored.append({
            "order_id": oid,
            "order": order,
            "score": score_info
        })
    
    scored.sort(key=lambda x: x["score"]["total_score"], reverse=True)
    return scored
