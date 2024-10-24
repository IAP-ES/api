from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.task import Task as TaskModel
from schemas.task import TaskCreate


def create_task(task: TaskCreate, user_id: str, db: Session = Depends(get_db)):
    """
    Create a task.

    :param db: Database session
    :param task: Task to create
    :return: Task created
    """

    new_task = TaskModel(**task.model_dump(), user_id=user_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


def get_tasks_by_user_id(user_id: str, db: Session = Depends(get_db)):
    """
    Get all tasks for a specific user.

    :param user_id: User ID
    :param db: Database session
    :return: List of tasks for the user
    """

    return (
        db.query(TaskModel)
        .filter(TaskModel.user_id == user_id)
        .order_by(TaskModel.created_at)
        .all()
    )
