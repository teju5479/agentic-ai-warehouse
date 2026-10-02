from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    workflow: Mapped[str] = mapped_column(String)
    tool_name: Mapped[str] = mapped_column(String)
    input_data: Mapped[str] = mapped_column(String)
    result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    policy_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    proposed_action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    approval_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state_changes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    outcome: Mapped[str] = mapped_column(String)
