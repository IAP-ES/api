import pytest
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer

from db.database import get_db
from main import app
from models.user import User as UserModel
from models.task import Task as TaskModel
from crud.task import (
    create_task,
    get_tasks_by_user_id,
    update_task,
    get_task_by_id,
    delete_task_by_id,
)
from schemas.task import TaskCreate, TaskUpdate

# Configuração de logging para facilitar a depuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do container MySQL para testes
my_sql_container = MySqlContainer(
    "mysql:8.0",
    root_password="test_root_password",
    dbname="test_db",
    username="test_username",
    password="test_password",
)


@pytest.fixture(name="session", scope="module")
def setup():
    """
    Fixture para iniciar o container MySQL e criar uma sessão do banco de dados.
    """
    # Inicia o container MySQL
    my_sql_container.start()
    connection_url = my_sql_container.get_connection_url()
    engine = create_engine(connection_url, connect_args={})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    UserModel.metadata.create_all(engine)  # Cria as tabelas do modelo

    # Sobrescreve a função get_db para usar a sessão do teste
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield SessionLocal  # Retorna a sessão para ser usada nos testes
    my_sql_container.stop()  # Para o container após os testes


@pytest.fixture(name="test_db", scope="module")
def create_test_db(session):
    """
    Fixture para criar uma instância do banco de dados para os testes.
    """
    db = session()  # Obtém uma nova sessão do banco de dados
    yield db  # Retorna a sessão para ser usada nos testes
    db.close()  # Fecha a sessão após os testes


@pytest.fixture(name="test_user", scope="function")
def create_test_user(test_db):
    """
    Fixture para criar um usuário de teste no banco de dados.
    """
    test_user = UserModel(
        id="id1",
        given_name="given_name1",
        family_name="family_name1",
        username="username1",
        email="email1",
    )
    test_db.add(test_user)
    test_db.commit()  # Salva o usuário no banco de dados
    yield test_user  # Retorna o usuário para ser usado nos testes

    # Remover as tasks associadas ao usuário antes de excluir o usuário
    test_db.query(TaskModel).filter(TaskModel.user_id == test_user.id).delete()
    test_db.delete(test_user)  # Remove o usuário após os testes
    test_db.commit()  # Comita as alterações no banco de dados


def test_create_task_with_priority(test_db, test_user: UserModel):
    """
    Testa a função de criação de uma Task no banco de dados.
    """
    task_data = TaskCreate(
        title="Test Task",
        description="This is a test task",
        priority="high",
    )

    # Chama a função para criar a task
    task_created = create_task(task=task_data, user_id=test_user.id, db=test_db)

    # Verifica se a Task foi salva no banco de dados
    task_in_db = (
        test_db.query(TaskModel).filter(TaskModel.id == task_created.id).first()
    )
    assert task_in_db is not None
    assert task_in_db.title == task_data.title
    assert task_in_db.description == task_data.description
    assert task_in_db.priority == task_data.priority
    assert task_in_db.user_id == test_user.id


def test_get_tasks_by_user_id(test_db, test_user: UserModel):
    """
    Testa a função de obter todas as Tasks de um usuário específico.
    """
    # Criar algumas Tasks associadas ao usuário de teste
    task_data_1 = TaskCreate(
        title="Test Task 1", description="This is test task 1", priority="low"
    )
    task_data_2 = TaskCreate(
        title="Test Task 2", description="This is test task 2", priority="high"
    )

    # Criar as Tasks no banco de dados
    create_task(task=task_data_1, user_id=test_user.id, db=test_db)
    create_task(task=task_data_2, user_id=test_user.id, db=test_db)

    # Chama a função para obter as tasks pelo user_id
    tasks = get_tasks_by_user_id(user_id=test_user.id, db=test_db)

    # Verifica se as tasks foram retornadas corretamente
    assert len(tasks) == 2  # Deve retornar 2 tasks
    assert tasks[0].title == task_data_1.title or tasks[0].title == task_data_2.title
    assert tasks[1].title == task_data_1.title or tasks[1].title == task_data_2.title


def test_delete_task_by_id(test_db, test_user: UserModel):
    """
    Testa a função de deletar uma Task pelo ID.
    """
    # Criar uma Task associada ao usuário de teste
    task_data = TaskCreate(
        title="Test Task",
        description="This is a test task",
        priority="low",
        user_id=test_user.id,
    )
    task_created = create_task(task=task_data, user_id=test_user.id, db=test_db)

    # Chama a função para deletar a task pelo ID
    delete_task_by_id(task_created.id, test_db)

    # Verifica se a Task foi removida do banco de dados
    task_in_db = (
        test_db.query(TaskModel).filter(TaskModel.id == task_created.id).first()
    )
    assert task_in_db is None  # A task não deve existir mais no banco de dados


def test_update_task(test_db, test_user: UserModel):
    """
    Testa a função de atualização de uma Task no banco de dados.
    """
    # Cria uma Task associada ao usuário de teste
    task_data = TaskCreate(
        title="Test Task",
        description="This is a test task",
        priority="low",
        user_id=test_user.id,  # Relaciona a task com o usuário de teste
    )
    task_created = create_task(task=task_data, user_id=test_user.id, db=test_db)

    # Atualiza os dados da Task
    task_data_update = TaskUpdate(
        title="Updated Task",
        description="This is an updated task",
        priority="high",
        status="done",
    )
    task_updated = update_task(
        task_id=task_created.id, task=task_data_update, db=test_db
    )

    # Verifica se a Task foi atualizada no banco de dados
    task_in_db = (
        test_db.query(TaskModel).filter(TaskModel.id == task_updated.id).first()
    )
    assert task_in_db is not None
    assert task_in_db.title == task_data_update.title
    assert task_in_db.description == task_data_update.description
    assert task_in_db.priority == task_data_update.priority
    assert task_in_db.status == task_data_update.status
    assert task_in_db.user_id == test_user.id


def test_get_task_by_id(test_db, test_user: UserModel):
    """
    Testa a função de obter uma Task pelo ID.
    """
    # Cria uma Task associada ao usuário de teste
    task_data = TaskCreate(
        title="Test Task",
        description="This is a test task",
        priority="low",
        user_id=test_user.id,  # Relaciona a task com o usuário de teste
    )
    task_created = create_task(task=task_data, user_id=test_user.id, db=test_db)

    # Chama a função para obter a task pelo ID
    task = get_task_by_id(task_id=task_created.id, db=test_db)

    # Verifica se a Task foi retornada corretamente
    assert task is not None
    assert task.title == task_data.title
    assert task.description == task_data.description
    assert task.priority == task_data.priority
    assert task.user_id == test_user.id
