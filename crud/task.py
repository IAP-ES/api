from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.task import Task as TaskModel
from schemas.task import TaskCreate, TaskUpdate


def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a task.

    :param db: Database session
    :param task: Task to create
    :return: Task created
    """

    task_db = TaskModel(**task.model_dump())
    db.add(task_db)
    db.commit()
    db.refresh(task_db)
    return task_db


def get_tasks_by_user_id(user_id: int, db: Session = Depends(get_db)):
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


def update_task(task_id: str, task: TaskUpdate, db: Session = Depends(get_db)):
    """
    Update a task.

    :param task_id: Task ID
    :param task: Task to update
    :param db: Database session
    :return: Task updated
    """

    task_db = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    task_db.title = task.title
    task_db.description = task.description
    db.commit()
    db.refresh(task_db)
    return task_db


def get_task_by_id(task_id: str, db: Session = Depends(get_db)):
    """
    Get a task by ID.

    :param task_id: Task ID
    :param db: Database session
    :return: Task
    """

    return db.query(TaskModel).filter(TaskModel.id == task_id).first()
