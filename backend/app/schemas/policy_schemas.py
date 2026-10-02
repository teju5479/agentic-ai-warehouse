from pydantic import BaseModel

class PolicySchema(BaseModel):
    policy_id: str
    title: str
    content: str
    category: str
    version: int
    
    model_config = {"from_attributes": True}

class PolicySearchRequest(BaseModel):
    query: str
    category: str | None = None
