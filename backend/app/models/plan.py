from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Plan(Base):
    __tablename__ = "plans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_plan_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default='DRAFT')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String)
    
    assignments: Mapped[List["Assignment"]] = relationship("Assignment", back_populates="plan")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("plans.plan_id"))
    order_id: Mapped[str] = mapped_column(String)
    picker_id: Mapped[str] = mapped_column(String)
    sequence: Mapped[int] = mapped_column(Integer)
    workload: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default='PENDING')
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    plan: Mapped["Plan"] = relationship("Plan", back_populates="assignments")
