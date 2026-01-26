from sqlalchemy import Integer, String, DateTime, func, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import datetime
from typing import List, Any


class Base(DeclarativeBase):
    pass


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    messages: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
