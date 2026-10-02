# Testing Plan

Automated testing is critical to ensure the safety and reliability of the warehouse agent system.

## Unit Tests (Pytest)

*   **Database Models**: Test creation, updates, and cascading deletes for all SQLAlchemy models (Order, Inventory, etc.).
*   **Pydantic Schemas**: Test validation logic (e.g., negative quantities, invalid status strings).
*   **Business Logic (Tools)**:
    *   Test `allocate_inventory` tool: Success case, failure case (insufficient stock), failure case (invalid order ID).
    *   Test `create_assignment` tool: Success case, failure case (picker already active), failure case (order not PLANNED).
    *   Test audit logging: Ensure every successful tool call creates an `AuditLog` entry.

## Integration Tests

*   **API Endpoints**: Test FastAPI routes for fetching state (GET /orders, GET /inventory).
*   **Agent Workflow Integration**:
    *   Mock the LLM provider.
    *   Feed a simulated tool call into the LangGraph state machine.
    *   Verify the graph transitions correctly, executes the tool, updates the database, and returns the result to the mocked LLM state.

## E2E Scenario Tests

These tests evaluate the agent's ability to handle the defined scenarios. We will use a mock LLM that returns deterministic tool calls for specific prompts.

1.  Setup clean database.
2.  Seed initial data (e.g., 30 units of SKU-A).
3.  Submit query: "Fulfill an order for 50 units of SKU-A".
4.  Assert that the system state reflects EXC-001 and the order remains PENDING.

Run tests using: `pytest` or `pytest -v --asyncio-mode=auto`
