from fastapi import HTTPException

from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import save_user, User as UserModel
from schemas.user import CreateUser


def new_user(user: CreateUser, db: Session = Depends(get_db)):
    return save_user(new_user=user, db=db)


def get_user_by_username(username: str, db: Session = Depends(get_db)):
    return db.query(UserModel).filter(UserModel.username == username).first()


def get_user(username: str, db: Session = Depends(get_db)):
    db_user = get_user_by_username(username, db)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
