from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Policy(Base):
    __tablename__ = "policies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
