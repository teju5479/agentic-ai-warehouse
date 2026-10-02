"""Warehouse Agent System - FastAPI Application.

A simulated warehouse operations platform containing two cooperating AI-enabled workflows:
1. Order Exception Resolver
2. Shift Task Planner

Both workflows use the same underlying warehouse state/database.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.models.order import Order
from app.seed.seed_database import seed_database
from app.models.database import SessionLocal, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup and seed if empty."""
    init_db()
    db = SessionLocal()
    try:
        if db.query(Order).count() == 0:
            seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Warehouse Agent System",
    description=(
        "Order Exception Resolver + Shift Planner - "
        "A warehouse agent system built on a simulated warehouse environment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from app.api.dashboard import router as dashboard_router
from app.api.orders import router as orders_router
from app.api.inventory import router as inventory_router
from app.api.shipments import router as shipments_router
from app.api.pickers import router as pickers_router
from app.api.exceptions import router as exceptions_router
from app.api.planner import router as planner_router
from app.api.scenarios import router as scenarios_router
from app.api.audit import router as audit_router
from app.api.policies import router as policies_router

app.include_router(dashboard_router)
app.include_router(orders_router)
app.include_router(inventory_router)
app.include_router(shipments_router)
app.include_router(pickers_router)
app.include_router(exceptions_router)
app.include_router(planner_router)
app.include_router(scenarios_router)
app.include_router(audit_router)
app.include_router(policies_router)


@app.get("/")
def root():
    return {
        "name": "Warehouse Agent System",
        "version": "1.0.0",
        "status": "running",
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini"),
        "endpoints": {
            "dashboard": "/api/dashboard",
            "orders": "/api/orders",
            "inventory": "/api/inventory",
            "shipments": "/api/shipments",
            "pickers": "/api/pickers",
            "exceptions": "/api/exceptions",
            "planner": "/api/planner",
            "scenarios": "/api/scenarios",
            "audit": "/api/audit",
            "policies": "/api/policies",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
