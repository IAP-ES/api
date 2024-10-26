from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
import uuid

from db.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(50), nullable=False)
    description = Column(String(200))
    status = Column(String(6), default="todo", nullable=False)
    priority = Column(String(5), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        index=True,
        default=datetime.datetime.now(),
        nullable=False,
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
