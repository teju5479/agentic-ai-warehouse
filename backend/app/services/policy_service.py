"""Policy management service.

Handles retrieval and search of operational policies.
"""
from sqlalchemy.orm import Session
from app.models.policy import Policy

def get_policy(db: Session, policy_id: str) -> Policy | None:
    """Retrieve policy by ID."""
    return db.query(Policy).filter(Policy.policy_id == policy_id).first()

def get_all_policies(db: Session) -> list[Policy]:
    """List all policies."""
    return db.query(Policy).all()

def search_policies(db: Session, query: str, category: str | None = None) -> list[Policy]:
    """Lightweight search using keyword matching on title and content."""
    db_query = db.query(Policy)
    if category:
        db_query = db_query.filter(Policy.category == category)
        
    policies = db_query.all()
    results = []
    
    query_words = set(query.lower().split())
    for policy in policies:
        text_to_search = f"{policy.title} {policy.content}".lower()
        # Simple match if any query word is in the text
        if any(word in text_to_search for word in query_words):
            results.append(policy)
            
    return results

def get_policies_for_exception(exception_type: str) -> list[str]:
    """Return relevant policy IDs based on exception type mapping."""
    mapping = {
        "INVENTORY_SHORTAGE": ["POL-001", "POL-003"],
        "PICKER_UNAVAILABLE": ["POL-002"],
        "SPILLAGE": ["POL-004"],
        "SYSTEM_FAILURE": ["POL-005"]
    }
    return mapping.get(exception_type.upper(), [])
