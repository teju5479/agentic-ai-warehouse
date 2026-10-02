# Reflection and Design Decisions

*This document serves as a log for key architectural and design decisions made during the project.*

## Decision 1: Strict Tool Layer

**Context**: LLMs are non-deterministic and prone to hallucination. Allowing direct database access is unsafe.
**Decision**: Implement a strict "Tools Layer" where every state change must go through a predefined Python function.
**Rationale**: This ensures that all business logic (SOPs, constraints) is evaluated deterministically by code, not by the LLM. It guarantees that the system remains in a valid state regardless of LLM output.

## Decision 2: LangGraph for Agent Workflows

**Context**: Need a robust way to manage agent state, loops, and human-in-the-loop interactions.
**Decision**: Use LangGraph.
**Rationale**: Provides explicit state management and control flow, which is superior to standard LangChain agents for complex, multi-step tasks like warehouse planning.

## Decision 3: Audit Logging

**Context**: Need traceability for every action taken by the autonomous agent.
**Decision**: Intercept every tool execution that mutates state and write to an `AuditLog` table.
**Rationale**: Crucial for trust and debugging in autonomous systems. Managers need to see exactly *why* and *how* the agent made a decision.
