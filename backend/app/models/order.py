from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    status: Mapped[str] = mapped_column(String, default='PENDING')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deadline: Mapped[datetime] = mapped_column(DateTime)
    priority: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    held_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    lines: Mapped[List["OrderLine"]] = relationship("OrderLine", back_populates="order")

class OrderLine(Base):
    __tablename__ = "order_lines"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id"))
    sku: Mapped[str] = mapped_column(String)
    requested_qty: Mapped[int] = mapped_column(Integer)
    picked_qty: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default='PENDING')
    
    order: Mapped["Order"] = relationship("Order", back_populates="lines")
