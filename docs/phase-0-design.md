# Phase 0 Design Document

## Entity Model

The core entities for the warehouse agent system are as follows:

*   **Order**: Represents a customer request for items. Contains `id`, `status` (PENDING, PLANNED, PROCESSING, COMPLETED, CANCELLED), `priority`, `created_at`.
*   **OrderLine**: Represents individual items within an order. Contains `id`, `order_id`, `sku`, `quantity`, `fulfilled_quantity`.
*   **Inventory**: Represents stock levels for a specific SKU. Contains `id`, `sku`, `location`, `quantity_on_hand`, `quantity_allocated`.
*   **Shipment**: Represents an outbound shipment containing fulfilled orders. Contains `id`, `destination`, `status`, `scheduled_date`.
*   **Picker**: Represents warehouse staff or robots capable of picking items. Contains `id`, `name`, `status` (IDLE, ACTIVE, UNAVAILABLE), `current_assignment_id`.
*   **Exception**: Represents anomalies or issues requiring intervention. Contains `id`, `type`, `description`, `status` (OPEN, RESOLVED, ESCALATED), `related_entity_id`, `resolution`.
*   **Plan**: Represents an actionable set of assignments. Contains `id`, `status`, `created_at`.
*   **Assignment**: Represents a specific task for a picker. Contains `id`, `plan_id`, `picker_id`, `order_id`, `status`.
*   **Policy**: Represents business rules. Contains `id`, `keyword`, `category`, `rule_text`.
*   **AuditLog**: Tracks state changes in the system. Contains `id`, `timestamp`, `action`, `entity_type`, `entity_id`, `user_id`, `details`.

## Relationships

*   Order (1) -> (N) OrderLine
*   Order (N) -> (1) Shipment
*   Order (1) <- (N) Assignment
*   Picker (1) -> (N) Assignment
*   Plan (1) -> (N) Assignment
*   Exception (N) -> (1) Any Entity (polymorphic relationship via related_entity_id)

## Data Assumptions

*   15-20 Orders
*   10-12 SKUs
*   10+ Inventory records (various locations)
*   10+ Shipments
*   4-5 Pickers

## Exception Types (EXC-001 through EXC-007)

1.  **EXC-001: Inventory Shortfall** - Insufficient inventory to fulfill an order line.
2.  **EXC-002: Duplicate Order** - An order with the same attributes as an existing active order is submitted.
3.  **EXC-003: Status Conflict** - Attempted operation on an entity in an invalid state (e.g., cancelling a COMPLETED order).
4.  **EXC-004: Invalid Quantity** - Requested quantity is negative or exceeds a reasonable limit.
5.  **EXC-005: Stale Shipment** - A shipment that hasn't departed within its scheduled window.
6.  **EXC-006: Conflicting Destination** - An order is assigned to a shipment with a different destination.
7.  **EXC-007: Missing Inventory Location** - Inventory record lacks a physical location in the warehouse.

## Autonomous vs Escalation Boundaries

*   **Autonomous Resolution**: The agent can autonomously resolve EXC-002 (by rejecting the new duplicate), EXC-004 (by rejecting or capping based on policy), and EXC-006 (by reassigning to correct shipment). It can also perform partial fulfillments for EXC-001 if policy allows.
*   **Needs Escalation**: EXC-001 (if policy dictates manual intervention for stock-outs), EXC-005 (requires physical inspection/logistics coordination), EXC-007 (requires data cleanup by human operator).

## Planning Policy

*   **Hard Constraints**:
    *   Cannot allocate more inventory than `quantity_on_hand` - `quantity_allocated`.
    *   Pickers can only have one active assignment at a time.
    *   Orders must belong to a shipment matching their destination.
*   **Priority Factors**:
    *   Order `priority` (High > Medium > Low).
    *   Age of the order (older orders get priority if priority levels are equal).
    *   Proximity of items to pickers (if spatial data is simulated).

## Failure Modes

*   LLM Hallucination (mitigated by strict tool schemas and business logic validation).
*   Concurrent modifications leading to race conditions (mitigated by SQLAlchemy transaction management).
*   Agent looping (mitigated by LangGraph `recursion_limit`).

## Shared SOP Rules (SOP-001 through SOP-010)

(Detailed in shared-policy.md)
