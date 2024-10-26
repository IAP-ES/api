import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import datetime

from main import app
from db.database import get_db
from auth.JWTBearer import JWTBearer, JWTAuthorizationCredentials
from auth.auth import get_current_user
from routers.task import auth
from schemas.task import TaskResponse

client = TestClient(app)

# JWT credentials mock
credentials = JWTAuthorizationCredentials(
    jwt_token="token",
    header={"kid": "some_kid"},
    claims={"sub": "user_id"},
    signature="signature",
    message="message",
)


# Mock for the database session
@pytest.fixture(scope="module")
def mock_db():
    db = Mock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db
    yield db


# Reset the mock database between tests
@pytest.fixture(autouse=True)
def reset_mock_db(mock_db):
    mock_db.reset_mock()


@patch("routers.task.get_user_by_username")  # Mock the get_user_by_id dependency
@patch("routers.task.create_task")  # Mock the create_task dependency
@patch.object(
    JWTBearer, "__call__", return_value=credentials
)  # Mock the JWTBearer dependency
def test_create_new_task(mock_jwt_bearer, mock_create_task, mock_get_user_by_username):
    """Test the create_new_task route, ensuring a task is created successfully."""

    app.dependency_overrides[auth] = lambda: credentials
    app.dependency_overrides[get_current_user] = lambda: "username1"

    # Set the Authorization header
    headers = {"Authorization": "Bearer token"}

    # Task data to send in the request
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "high",
    }

    mock_task = TaskResponse(
        id="1",
        title="Test Task",
        description="Test Description",
        status="todo",
        priority="high",
        created_at=datetime.datetime.now(),
    )

    mock_create_task.return_value = mock_task

    # Make the request to create a new task
    response = client.post(
        "/tasks",
        json=task_data,
        headers=headers,
    )

    # Assert the response status code is 201 (Created)
    assert response.status_code == 201

    # Assert that the response JSON contains the correct task data
    task_created = response.json()
    assert task_created["id"] == mock_task.id
    assert task_created["title"] == task_data["title"]
    assert task_created["description"] == task_data["description"]
    assert task_created["status"] == "todo"
    assert task_created["priority"] == "high"
    assert task_created["created_at"] == mock_task.created_at.isoformat()

    app.dependency_overrides = {}


@patch("routers.task.get_user_by_username")  # Mock the create_task dependency
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_create_new_task_user_not_found(mock_jwt_bearer, mock_get_user_by_username):
    """Test the create_new_task route when the user does not exist."""

    app.dependency_overrides[auth] = lambda: credentials
    app.dependency_overrides[get_current_user] = lambda: "username1"

    headers = {"Authorization": "Bearer token"}

    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "high",
    }

    mock_get_user_by_username.return_value = None

    # Make the request
    response = client.post(
        "/tasks",
        json=task_data,
        headers=headers,
    )

    # Assert 404 status code
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    app.dependency_overrides = {}


@patch(
    "routers.task.get_user_by_username", return_value=Exception
)  # Mock the get_user_by_id dependency
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_create_new_task_internal_server_error(
    mock_jwt_bearer, mock_get_user_by_username
):
    """Test create_new_task route when there's an internal server error."""

    # Mock JWT auth
    app.dependency_overrides[auth] = lambda: credentials
    app.dependency_overrides[get_current_user] = lambda: "username1"

    # Set the Authorization header
    headers = {"Authorization": "Bearer token"}

    # Data to be sent in the request
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "high",
    }

    # Make the request to create a new task
    response = client.post(
        "/tasks",
        json=task_data,
        headers=headers,
    )

    # Assert the status code is 500
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error while creating the task"

    # Clean up overrides
    app.dependency_overrides = {}


@patch("routers.task.get_user_by_username")  # Mock the get_user_by_username dependency
@patch(
    "routers.task.create_task", side_effect=ValueError("Invalid task data")
)  # Simulate ValueError in create_task
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_create_new_task_value_error(
    mock_jwt_bearer, mock_create_task, mock_get_user_by_username
):
    """Test the create_new_task route when there is a ValueError (e.g., invalid task data)."""

    # Mock the current user
    app.dependency_overrides[auth] = lambda: credentials
    app.dependency_overrides[get_current_user] = lambda: "username1"

    headers = {"Authorization": "Bearer token"}

    # Data that will trigger the ValueError in create_task
    task_data = {
        "title": "",  # Example of invalid data that could trigger a ValueError
        "description": "Test Description",
        "priority": "invalid_priority",  # Example of an invalid priority
    }

    # Simulate valid user
    mock_get_user_by_username.return_value = Mock(id="1")

    # Make the request
    response = client.post(
        "/tasks",
        json=task_data,
        headers=headers,
    )

    # Assert 400 status code for ValueError
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid task data"

    # Clean up overrides
    app.dependency_overrides = {}


# Test for get tasks by user route


@patch("routers.task.get_tasks_by_user_id")  # Mock get_tasks_by_user_id
@patch("routers.task.get_user_by_username")  # Mock get_user_by_username
@patch.object(
    JWTBearer, "__call__", return_value=credentials
)  # Mock the JWTBearer dependency
def test_get_tasks_by_user(
    mock_jwt_bearer, mock_get_user_by_username, mock_get_tasks_by_user_id
):
    """Test the get_tasks_by_user route, ensuring it returns tasks for the user."""

    # Mock the current user
    app.dependency_overrides[auth] = lambda: credentials
    app.dependency_overrides[get_current_user] = lambda: "username1"

    # Mock the tasks returned by get_tasks_by_user_id

    mock_task1 = TaskResponse(
        id="1",
        title="Task 1",
        description="Description 1",
        status="todo",
        priority="high",
        created_at=datetime.datetime.now(),
    )
    mock_task2 = TaskResponse(
        id="2",
        title="Task 2",
        description="Description 2",
        status="todo",
        priority="low",
        created_at=datetime.datetime.now(),
    )
    mock_get_tasks_by_user_id.return_value = [mock_task1, mock_task2]

    # Make the request to the endpoint
    response = client.get("/tasks")

    # Check the response status code
    assert response.status_code == 200

    # Check the content of the response
    tasks = response.json()
    assert len(tasks) == 2
    assert tasks[0]["title"] == mock_task1.title
    assert tasks[0]["description"] == mock_task1.description
    assert tasks[0]["status"] == mock_task1.status
    assert tasks[0]["priority"] == mock_task1.priority
    assert tasks[1]["title"] == mock_task2.title
    assert tasks[1]["description"] == mock_task2.description
    assert tasks[1]["status"] == mock_task2.status
    assert tasks[1]["priority"] == mock_task2.priority

    # Reset the overrides to not interfere with other tests
    app.dependency_overrides = {}


@patch("routers.task.get_user_by_username")
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_get_tasks_user_not_found(mock_jwt_bearer, mock_get_user_by_username):
    """Test the get_tasks_by_user route when the user is not found."""

    app.dependency_overrides[auth] = lambda: credentials
    app.dependency_overrides[get_current_user] = lambda: "non_existing_username"

    # Simulate get_user_by_username returning None (user not found)
    mock_get_user_by_username.return_value = None

    # Make the request
    response = client.get("/tasks")

    # Assert 404 status code
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    app.dependency_overrides = {}


@patch("routers.task.get_tasks_by_user_id")
@patch("routers.task.get_user_by_username")
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_get_tasks_internal_server_error(
    mock_jwt_bearer, mock_get_user_by_username, mock_get_tasks_by_user_id
):
    """Test get_tasks_by_user route when there's an internal server error."""

    app.dependency_overrides[auth] = lambda: credentials
    app.dependency_overrides[get_current_user] = lambda: "username1"

    # Simulate a valid user
    mock_get_user_by_username.return_value = Mock(id="1")

    # Simulate an exception during task retrieval
    mock_get_tasks_by_user_id.side_effect = Exception("Simulated DB error")

    # Make the request
    response = client.get("/tasks")

    # Assert 500 status code
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error while getting tasks"

    app.dependency_overrides = {}


@patch("routers.task.get_task_by_id")  # Mock the get_task_by_id dependency
@patch("routers.task.update_task")  # Mock the update_task dependency
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_update_task_success(mock_jwt_bearer, mock_update_task, mock_get_task_by_id):
    """Test the update_task route, ensuring a task is updated successfully."""

    app.dependency_overrides[auth] = lambda: credentials

    # Task ID and data to be updated
    task_id = "1"
    updated_task_data = {
        "title": "Updated Task",
        "description": "Updated Description",
        "status": "done",
        "priority": "high",
    }

    mock_task = TaskResponse(
        id=task_id,
        title="Updated Task",
        description="Updated Description",
        status="done",
        priority="high",
        created_at=datetime.datetime.now(),
    )

    mock_update_task.return_value = mock_task

    headers = {"Authorization": "Bearer token"}

    # Make the request to update the task
    response = client.put(
        f"/tasks/{task_id}",
        json=updated_task_data,
        headers=headers,
    )

    # Assert the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert the response contains the updated task data
    updated_task = response.json()
    assert updated_task["id"] == mock_task.id
    assert updated_task["title"] == updated_task_data["title"]
    assert updated_task["description"] == updated_task_data["description"]
    assert updated_task["status"] == "done"
    assert updated_task["priority"] == "high"

    app.dependency_overrides = {}


@patch("routers.task.get_task_by_id", return_value=None)
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_update_task_not_found(mock_jwt_bearer, mock_update_task):
    """Test update_task route when the task does not exist."""

    app.dependency_overrides[auth] = lambda: credentials

    task_id = "non_existing_task_id"
    updated_task_data = {
        "title": "Updated Task",
        "description": "Updated Description",
        "status": "done",
        "priority": "high",
    }

    headers = {"Authorization": "Bearer token"}

    # Make the request to update a non-existing task
    response = client.put(
        f"/tasks/{task_id}",
        json=updated_task_data,
        headers=headers,
    )

    # Assert 404 status code
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"

    app.dependency_overrides = {}


@patch("routers.task.update_task", side_effect=Exception("Simulated DB error"))
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_update_task_internal_server_error(mock_jwt_bearer, mock_update_task):
    """Test update_task route when there's an internal server error."""

    app.dependency_overrides[auth] = lambda: credentials

    task_id = "1"
    updated_task_data = {
        "title": "Updated Task",
        "description": "Updated Description",
        "status": "done",
        "priority": "high",
    }

    headers = {"Authorization": "Bearer token"}

    # Make the request to update the task, but simulate an internal server error
    response = client.put(
        f"/tasks/{task_id}",
        json=updated_task_data,
        headers=headers,
    )

    # Assert 500 status code
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error while updating the task"

    app.dependency_overrides = {}


@patch("routers.task.get_task_by_id")  # Mock the get_task_by_id dependency
@patch(
    "routers.task.update_task", side_effect=ValueError("Invalid update data")
)  # Simulate ValueError in update_task
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_update_task_value_error(
    mock_jwt_bearer, mock_update_task, mock_get_task_by_id
):
    """Test the update_task route when there is a ValueError (e.g., invalid update data)."""

    # Mock the current user
    app.dependency_overrides[auth] = lambda: credentials

    # Task ID and invalid data that will trigger a ValueError in update_task
    task_id = "1"
    updated_task_data = {
        "title": "",  # Example of invalid data that could trigger a ValueError
        "description": "Updated Description",
        "status": "invalid_status",  # Example of an invalid status
        "priority": "high",
    }

    # Simulate existing task
    mock_get_task_by_id.return_value = Mock(id=task_id)

    headers = {"Authorization": "Bearer token"}

    # Make the request
    response = client.put(
        f"/tasks/{task_id}",
        json=updated_task_data,
        headers=headers,
    )

    # Assert 400 status code for ValueError
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid update data"

    # Clean up overrides
    app.dependency_overrides = {}


@patch("routers.task.get_task_by_id")  # Mock get_task_by_id
@patch("routers.task.delete_task_by_id")  # Mock delete_task_by_id
@patch.object(
    JWTBearer, "__call__", return_value=credentials
)  # Mock the JWTBearer dependency
def test_delete_task_by_id_success(
    mock_jwt_bearer, mock_delete_task_by_id, mock_get_task_by_id
):
    """Test successful deletion of a task."""

    app.dependency_overrides[auth] = lambda: credentials

    # Task ID for the task to delete
    task_id = "1"

    # Simulate finding the task
    mock_task = Mock(id=task_id)
    mock_get_task_by_id.return_value = mock_task

    # Make the delete request
    response = client.delete(f"/tasks/{task_id}")

    # Assert the response status code is 204 (No Content)
    assert response.status_code == 204

    # Capture the actual DB session passed in the function call
    # Use the actual db object passed in the test to assert
    mock_delete_task_by_id.assert_called_once()

    # Reset dependency overrides
    app.dependency_overrides = {}


@patch("routers.task.get_task_by_id")  # Mock get_task_by_id
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_delete_task_by_id_not_found(mock_jwt_bearer, mock_get_task_by_id):
    """Test deletion when task is not found (404 error)."""

    app.dependency_overrides[auth] = lambda: credentials

    task_id = "non_existing_task_id"

    # Simulate task not being found
    mock_get_task_by_id.return_value = None

    # Make the delete request
    response = client.delete(f"/tasks/{task_id}")

    # Assert 404 status code
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {task_id} not found"

    app.dependency_overrides = {}


@patch("routers.task.get_task_by_id", return_value=Mock(id="1"))  # Mock get_task_by_id
@patch(
    "routers.task.delete_task_by_id", side_effect=Exception("Simulated DB error")
)  # Mock delete_task_by_id
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_delete_task_by_id_internal_server_error(
    mock_jwt_bearer, mock_delete_task_by_id, mock_get_task_by_id
):
    """Test deletion when there's an internal server error."""

    app.dependency_overrides[auth] = lambda: credentials

    task_id = "1"

    # Make the delete request
    response = client.delete(f"/tasks/{task_id}")

    # Assert 500 status code
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error while deleting the task"

    app.dependency_overrides = {}
