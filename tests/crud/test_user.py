import pytest
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer

from db.database import get_db
from main import app
from models.user import User as UserModel
from schemas.user import UserCreate
from crud.user import create_user, get_user_by_username, get_user_by_email

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
    test_db.delete(test_user)  # Remove o usuário após os testes
    test_db.commit()  # Comita as alterações no banco de dados


def test_create_user(test_db):
    """
    Testa a criação de um usuário no banco de dados.
    """
    user_data = UserCreate(
        id="id2",
        given_name="given_name2",
        family_name="family_name2",
        username="username2",
        email="email2",
    )
    created_user = create_user(
        user_data, test_db
    )  # Chama a função para criar o usuário

    # Verifica se o usuário foi criado corretamente
    assert created_user is not None
    assert created_user.username == "username2"
    assert created_user.email == "email2"
    assert created_user.given_name == "given_name2"
    assert created_user.family_name == "family_name2"


def test_get_user_by_username_found(test_db, test_user):
    """
    Testa a busca por um usuário usando o nome de usuário que existe no banco de dados.
    """
    found_user = get_user_by_username(test_user.username, test_db)  # Busca pelo usuário

    # Verifica se o usuário encontrado corresponde ao esperado
    assert found_user is not None
    assert found_user.id == test_user.id


def test_get_user_by_username_not_found(test_db):
    """
    Testa a busca por um usuário usando um nome de usuário que não existe no banco de dados.
    """
    found_user = get_user_by_username(
        "not_exist", test_db
    )  # Tenta buscar um usuário inexistente
    assert found_user is None  # Verifica que nenhum usuário foi encontrado


def test_get_user_by_email_found(test_db, test_user):
    """
    Testa a busca por um usuário usando um email que existe no banco de dados.
    """
    found_user = get_user_by_email(test_user.email, test_db)  # Busca pelo usuário

    # Verifica se o usuário encontrado corresponde ao esperado
    assert found_user is not None
    assert found_user.id == test_user.id


def test_get_user_by_email_not_found(test_db):
    """
    Testa a busca por um usuário usando um email que não existe no banco de dados.
    """
    found_user = get_user_by_email(
        "not_exist@email.com", test_db
    )  # Tenta buscar um usuário inexistente
    assert found_user is None  # Verifica que nenhum usuário foi encontrado
