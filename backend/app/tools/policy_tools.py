"""Policy tools for agent workflows."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.policy import Policy
from app.services.audit_service import create_audit_entry

def get_policy(db: Session, policy_id: str, run_id: str = "", workflow: str = "") -> dict:
    """Retrieve a specific policy by ID."""
    policy = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not policy:
        return {"success": False, "error": f"Policy {policy_id} not found"}
        
    result = {
        "success": True,
        "policy": {
            "policy_id": policy.policy_id,
            "title": policy.title,
            "content": policy.content,
            "category": policy.category,
            "version": policy.version
        }
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "get_policy", {"policy_id": policy_id}, result={"policy_id": policy_id}, outcome="SUCCESS")
        
    return result

def search_policies(db: Session, query: str = None, category: str = None, run_id: str = "", workflow: str = "") -> dict:
    """Search policies by keyword matching in title/content, optional category filter."""
    db_query = db.query(Policy)
    
    if query:
        words = query.split()
        for word in words:
            search_term = f"%{word}%"
            db_query = db_query.filter(or_(
                Policy.title.ilike(search_term),
                Policy.content.ilike(search_term)
            ))
            
    if category:
        db_query = db_query.filter(Policy.category == category)
        
    policies = db_query.all()
    
    result = {
        "success": True,
        "policies": [
            {
                "policy_id": p.policy_id,
                "title": p.title,
                "content": p.content,
                "category": p.category,
                "version": p.version
            }
            for p in policies
        ],
        "count": len(policies)
    }
    
    if run_id:
        create_audit_entry(db, run_id, workflow, "search_policies", {"query": query, "category": category}, result={"count": len(policies)}, outcome="SUCCESS")
        
    return result
