from typing import Optional
from sqlalchemy import Column, String, DateTime
from sqlalchemy import String
import datetime
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)
    given_name = Column(String(200), index=True, nullable=False)
    family_name = Column(String(200), index=True, nullable=False)
    username = Column(String(200), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        index=True,
        default=datetime.datetime.now(),
        nullable=False,
    )
