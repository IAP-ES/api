from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User as UserModel
from schemas.user import UserCreate


def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a user.

    :param db: Database session
    :param ticket: Ticket to create
    :return: Ticket created
    """
    user_db = UserModel(**user.model_dump())
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return user_db


def get_user_by_username(user_username: str, db: Session = Depends(get_db)):
    """
    Get a user by username.

    :param db: Database session
    :param user_username: Username of the user
    :return: User
    """
    return db.query(UserModel).filter(UserModel.username == user_username).first()


def get_user_by_email(user_email: str, db: Session = Depends(get_db)):
    """
    Get a user by email.

    :param db: Database session
    :param user_email: Email of the user
    :return: User
    """
    return db.query(UserModel).filter(UserModel.email == user_email).first()


def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    """
    Get a user by ID.

    :param db: Database session
    :param user_id: ID of the user
    :return: User
    """
    return db.query(UserModel).filter(UserModel.id == user_id).first()
