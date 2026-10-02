from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import get_db
from app.models.policy import Policy
from app.schemas.policy_schemas import PolicySchema

router = APIRouter(prefix="/api/policies", tags=["Policies"])

class PolicySearchQuery(BaseModel):
    query: str
    category: str | None = None

@router.get("", response_model=list[PolicySchema])
def list_policies(db: Session = Depends(get_db)):
    policies = db.query(Policy).all()
    return [PolicySchema.model_validate(p) for p in policies]

@router.get("/{policy_id}", response_model=PolicySchema)
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(404, f"Policy {policy_id} not found")
    return PolicySchema.model_validate(policy)

@router.post("/search", response_model=list[PolicySchema])
def search_policies(search: PolicySearchQuery, db: Session = Depends(get_db)):
    query = db.query(Policy).filter(Policy.content.ilike(f"%{search.query}%"))
    if search.category:
        query = query.filter(Policy.category == search.category)
    
    policies = query.all()
    return [PolicySchema.model_validate(p) for p in policies]
