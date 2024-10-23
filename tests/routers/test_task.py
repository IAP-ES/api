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


# Test for create_new_task route
@patch("routers.task.create_task")  # Mock the create_task dependency
@patch.object(
    JWTBearer, "__call__", return_value=credentials
)  # Mock the JWTBearer dependency
def test_create_new_task(mock_jwt_bearer, mock_create_task):
    """Test the create_new_task route, ensuring a task is created successfully."""

    app.dependency_overrides[auth] = lambda: credentials

    # Set the Authorization header
    headers = {"Authorization": "Bearer token"}

    # Task data to send in the request
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "user_id": "1",
    }

    mock_task = TaskResponse(
        id="1",
        title="Test Task",
        description="Test Description",
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
    assert task_created["created_at"] == mock_task.created_at.isoformat()

    app.dependency_overrides = {}


@patch("routers.task.get_user_by_id")  # Mock the create_task dependency
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_create_new_task_user_not_found(mock_jwt_bearer, mock_get_user_by_id):
    """Test the create_new_task route when the user does not exist."""

    app.dependency_overrides[auth] = lambda: credentials

    headers = {"Authorization": "Bearer token"}

    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "user_id": "non_existing_user_id",
    }

    mock_get_user_by_id.return_value = None

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
    "routers.task.get_user_by_id", return_value=Exception
)  # Mock the get_user_by_id dependency
@patch.object(JWTBearer, "__call__", return_value=credentials)
def test_create_new_task_internal_server_error(mock_jwt_bearer, mock_get_user_by_id):
    """Test create_new_task route when there's an internal server error."""

    # Mock JWT auth
    app.dependency_overrides[auth] = lambda: credentials

    # Set the Authorization header
    headers = {"Authorization": "Bearer token"}

    # Data to be sent in the request
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "user_id": "1",
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
        created_at=datetime.datetime.now(),
    )
    mock_task2 = TaskResponse(
        id="2",
        title="Task 2",
        description="Description 2",
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
    assert tasks[1]["title"] == mock_task2.title
    assert tasks[1]["description"] == mock_task2.description

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