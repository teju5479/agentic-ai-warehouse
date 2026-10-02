from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Picker(Base):
    __tablename__ = "pickers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    picker_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    availability: Mapped[str] = mapped_column(String, default='AVAILABLE')
    capacity: Mapped[int] = mapped_column(Integer)
    current_workload: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str] = mapped_column(String)
    skills: Mapped[str] = mapped_column(String)
