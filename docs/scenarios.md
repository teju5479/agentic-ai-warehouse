# Scenarios

This document outlines various scenarios the agent is expected to handle, including exceptions, planning, and replanning.

## Exception Scenarios

1.  **EXC-001: Inventory Shortfall**
    *   *Trigger*: Order 101 requests 50 units of SKU-A. Only 30 units are available.
    *   *Expected Behavior*: Agent attempts allocation, tool rejects due to insufficient stock. Agent catches error, creates EXC-001, and leaves Order 101 in PENDING state. Escalate to user.
2.  **EXC-002: Duplicate Order**
    *   *Trigger*: Order 102 is received. It perfectly matches Order 99 from 2 hours ago.
    *   *Expected Behavior*: Agent detects duplicate based on SOP-008. Creates EXC-002. Rejects creation of Order 102.
3.  **EXC-003: Status Conflict**
    *   *Trigger*: User asks the agent to cancel Order 103, which is currently marked as PROCESSING.
    *   *Expected Behavior*: Agent attempts cancellation tool. Tool rejects based on SOP-006. Agent informs user that it requires manager escalation.
4.  **EXC-004: Invalid Quantity**
    *   *Trigger*: Order 104 is received requesting -5 units of SKU-B.
    *   *Expected Behavior*: Input validation (Pydantic) fails before business logic. Agent receives validation error and rejects the order request.
5.  **EXC-005: Stale Shipment**
    *   *Trigger*: Scheduled check detects Shipment 200 was scheduled for 10:00 AM; current time is 1:00 PM, status is PENDING.
    *   *Expected Behavior*: Agent creates EXC-005. Notifies logistics team (simulated via log/message).
6.  **EXC-006: Conflicting Destination**
    *   *Trigger*: Agent attempts to assign Order 105 (Destination: East Coast) to Shipment 201 (Destination: West Coast).
    *   *Expected Behavior*: Tool rejects assignment based on SOP-005. Agent must retry with a valid shipment.
7.  **EXC-007: Missing Inventory Location**
    *   *Trigger*: Agent attempts to plan picking for SKU-C, but its location field is NULL.
    *   *Expected Behavior*: Agent identifies missing location data, creates EXC-007, and halts planning for that specific order line until resolved.

## Planning Scenarios

*   **Nominal Planning**: 3 new PENDING orders, sufficient inventory, 2 idle pickers.
    *   *Expected Behavior*: Agent successfully allocates inventory (updating state to PLANNED), creates Assignments for the pickers, and groups them into a Plan.

## Replanning Scenarios

*   **Picker Offline**: A plan exists. Picker 1 suddenly goes UNAVAILABLE.
    *   *Expected Behavior*: Agent detects picker status change. Cancels PENDING assignments for Picker 1. Re-evaluates active plans and assigns tasks to remaining idle pickers based on priority.
