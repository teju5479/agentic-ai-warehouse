"""Shared test fixtures."""
import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.database import Base
from app.seed.seed_database import seed_database


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Seed with test data
    seed_database(session)
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def run_id():
    """Generate a test run ID."""
    return "TEST-RUN-001"
