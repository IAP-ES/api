import datetime

from fastapi import Depends
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session

from db.database import Base, get_db
from schemas.user import CreateUser


class User(Base):
    __tablename__ = "user"

    id = Column(String(50), primary_key=True, index=True)
    given_name = Column(String(200), index=True, nullable=False)
    family_name = Column(String(200), index=True, nullable=False)
    username = Column(String(200), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    is_active = Column(Integer, index=True, default=True, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        index=True,
        default=datetime.datetime.now(),
        nullable=False,
    )

    def active(self, db: Session = Depends(get_db)):
        self.is_active = True
        self.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(self)
        return self


def save_user(new_user: CreateUser, db: Session = Depends(get_db)):

    db_user = User(
        id=new_user.id,
        given_name=new_user.given_name,
        family_name=new_user.family_name,
        username=new_user.username,
        email=new_user.email,
        is_active=False,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
