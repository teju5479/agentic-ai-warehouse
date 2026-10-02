from pydantic import BaseModel
from typing import Optional
import json

class PickerSchema(BaseModel):
    picker_id: str
    name: str
    availability: str
    capacity: int
    current_workload: int
    remaining_capacity: int = 0
    location: str
    skills: list[str] = []
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def from_db(cls, picker):
        skills = json.loads(picker.skills) if picker.skills else []
        return cls(
            picker_id=picker.picker_id,
            name=picker.name,
            availability=picker.availability,
            capacity=picker.capacity,
            current_workload=picker.current_workload,
            remaining_capacity=picker.capacity - picker.current_workload,
            location=picker.location,
            skills=skills
        )

class PickerUpdateRequest(BaseModel):
    availability: Optional[str] = None
    current_workload: Optional[int] = None

PickerUpdateSchema = PickerUpdateRequest
