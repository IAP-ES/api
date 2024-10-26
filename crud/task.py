from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime

from db.database import get_db
from models.task import Task as TaskModel
from schemas.task import TaskCreate, TaskUpdate


def create_task(task: TaskCreate, user_id: str, db: Session = Depends(get_db)):
    """
    Create a task.

    :param db: Database session
    :param task: Task to create
    :return: Task created
    """

    new_task = TaskModel(**task.model_dump(), user_id=user_id)
    if new_task.deadline and new_task.deadline < datetime.now():
        raise ValueError("Deadline must be in the future")
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


def delete_task_by_id(task_id: str, db: Session = Depends(get_db)):
    """
    Delete a task by ID.

    :param task_id: Task ID
    :param db: Database session
    :return: None
    """

    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()

    if not task:
        return None

    db.delete(task)
    db.commit()
    return None


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
    task_db.status = task.status
    task_db.priority = task.priority
    if task.deadline:
        if task.deadline < datetime.now():
            raise ValueError("Deadline must be in the future")
        task_db.deadline = task.deadline
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
