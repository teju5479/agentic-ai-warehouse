from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class ExceptionRecord(Base):
    __tablename__ = "exceptions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exception_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    order_id: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default='OPEN')
    severity: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    evidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    policy_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    proposed_action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
