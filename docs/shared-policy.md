# Shared Policies (SOPs)

This document details the standard operating procedures that govern warehouse operations and agent behavior.

*   **SOP-001: Inventory Allocation**: Inventory must be allocated immediately when an order is PLANNED. The `quantity_allocated` must increase, and the available quantity (`quantity_on_hand` - `quantity_allocated`) must not fall below zero.
*   **SOP-002: Shortfall Handling**: If an order requires more inventory than is available, generate an EXC-001 (Inventory Shortfall) exception. Do not allocate partial inventory unless explicitly requested by a manager override.
*   **SOP-003: Order Priority**: When generating plans, HIGH priority orders must be assigned to pickers before MEDIUM or LOW priority orders, regardless of creation time.
*   **SOP-004: Picker Capacity**: A picker can only have one ACTIVE assignment. New assignments can be queued in PENDING state, but only one can be actively processed.
*   **SOP-005: Shipment Validation**: Before an order is assigned to a shipment, the order's destination region must match the shipment's designated region.
*   **SOP-006: Cancellation Policy**: Orders can only be cancelled if they are in PENDING or PLANNED state. Once PROCESSING (picking has started), they cannot be cancelled autonomously; escalate to manager.
*   **SOP-007: Stale Shipment Protocol**: Shipments scheduled for departure more than 2 hours ago but still in PENDING state must trigger an EXC-005. The agent should escalate this to the logistics team.
*   **SOP-008: Duplicate Detection**: If an incoming order matches the exact SKUs, quantities, and customer ID of an order placed within the last 24 hours, flag it as EXC-002 and pause processing until confirmed.
*   **SOP-009: Unknown Item Handling**: If an order requests a SKU that does not exist in the inventory master data, reject the order immediately with an informative message; do not create an exception.
*   **SOP-010: Audit Mandate**: Every tool execution that modifies the state of Orders, Inventory, Shipments, or Pickers must result in a corresponding AuditLog entry detailing the change, the tool used, and the justification.
