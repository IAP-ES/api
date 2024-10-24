import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db
from crud.task import (
    create_task,
    get_tasks_by_user_id,
    delete_task_by_id,
    get_task_by_id,
    update_task,
)
from crud.user import get_user_by_id, get_user_by_username
from schemas.task import TaskCreate, TaskResponse, TaskUpdate
from auth.auth import jwks, get_current_user
from auth.JWTBearer import JWTBearer

router = APIRouter(tags=["Tasks"])

auth = JWTBearer(jwks)


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth)],
)
async def create_new_task(
    task_data: TaskCreate,
    user_username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new task for a specific user.

    :param task_data: Task data to create
    :param user_id: User ID
    :param db: Database session
    :return: Task created

    :raises HTTPException: If the user does not exist or if there is an internal server error
    :raises Exception: If there is an internal server error
    """

    # Check if the user exists in the database
    user = get_user_by_username(user_username, db=db)

    if not user:
        logging.error(f"User with username {user_username} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        # Create a new task
        new_task = create_task(task=task_data, user_id=user.id, db=db)

        # If successful, return the task in the response
        return new_task

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to maintain the status code
        raise http_exc

    except Exception as e:
        logging.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating the task",
        )


# get tasks by user
@router.get(
    "/tasks",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth)],
)
async def get_tasks_by_user(
    user_username: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get all tasks for a specific user.

    :param user_username: The username of the user
    :param db: Database session
    :return: List of tasks for the user

    :raises HTTPException: If the user does not exist or if there is an internal server error
    :raises Exception: If there is an internal server error
    """

    # Check if the user exists in the database
    user = get_user_by_username(user_username, db=db)

    if not user:
        logging.error(f"User '{user_username}' not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        # Get all tasks for the user
        tasks = get_tasks_by_user_id(user_id=user.id, db=db)

        # If successful, return the tasks in the response
        return tasks

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to maintain the status code
        raise http_exc

    except Exception as e:
        logging.error(f"Failed to get tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting tasks",
        )


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth)],
)
async def delete_task_by_id_route(task_id: str, db: Session = Depends(get_db)):
    """
    Delete a task by ID.

    :param task_id: Task ID
    :param db: Database session
    :return: None

    :raises HTTPException: If the task does not exist or if there is an internal server error
    :raises Exception: If there is an internal server error
    """

    try:
        task = get_task_by_id(task_id=task_id, db=db)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        # Delete the task by ID
        delete_task_by_id(task_id=task_id, db=db)

        # If successful, return None
        return None

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to maintain the status code
        raise http_exc

    except Exception as e:
        logging.error(f"Failed to delete task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting the task",
        )


@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth)],
)
async def update_task_route(
    task_id: str, task_data: TaskUpdate, db: Session = Depends(get_db)
):
    """
    Update a task.

    :param task_id: Task ID
    :param task_data: Task data to update
    :param db: Database session
    :return: Task updated

    :raises HTTPException: If the task does not exist or if there is an internal server error
    :raises Exception: If there is an internal server error
    """

    try:
        task = get_task_by_id(task_id=task_id, db=db)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )

        # Update the task
        updated_task = update_task(task_id=task_id, task=task_data, db=db)

        # If successful, return the updated task in the response
        return updated_task

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to maintain the status code
        raise http_exc

    except Exception as e:
        logging.error(f"Failed to update task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating the task",
        )
