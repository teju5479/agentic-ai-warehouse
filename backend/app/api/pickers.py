from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.picker import Picker
from app.schemas.picker_schemas import PickerSchema, PickerUpdateSchema

router = APIRouter(prefix="/api/pickers", tags=["Pickers"])

@router.get("", response_model=list[PickerSchema])
def list_pickers(db: Session = Depends(get_db)):
    pickers = db.query(Picker).all()
    return [PickerSchema.from_db(p) for p in pickers]

@router.get("/{picker_id}", response_model=PickerSchema)
def get_picker(picker_id: str, db: Session = Depends(get_db)):
    picker = db.query(Picker).filter(Picker.picker_id == picker_id).first()
    if not picker:
        raise HTTPException(404, f"Picker {picker_id} not found")
    return PickerSchema.from_db(picker)

@router.patch("/{picker_id}", response_model=PickerSchema)
def update_picker(picker_id: str, update_data: PickerUpdateSchema, db: Session = Depends(get_db)):
    picker = db.query(Picker).filter(Picker.picker_id == picker_id).first()
    if not picker:
        raise HTTPException(404, f"Picker {picker_id} not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(picker, key, value)
        
    db.commit()
    db.refresh(picker)
    return PickerSchema.from_db(picker)
