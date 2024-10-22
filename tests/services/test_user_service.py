import base64
import os
import pytest
import logging
from unittest.mock import patch

from auth.user_auth import auth_with_code, user_info_with_token, logout_with_token

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis Cognito
cognito_user_client_id = "client_id"
cognito_user_client_secret = "client_secret"
cognito_token_endpoint = "http://token_endpoint"

# Cabeçalhos de autenticação baseados no client_id e client_secret
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {base64.b64encode(f'{cognito_user_client_id}:{cognito_user_client_secret}'.encode()).decode()}",
}


# Classe para simular a resposta do requests.post
class RequestsMockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = "error reason"  # Pode ser útil para debugar mensagens de erro

    def json(self):
        return self.json_data


# Fixture que configura as variáveis de ambiente necessárias
@pytest.fixture(autouse=True, scope="module")
def setup_environ():
    os.environ["COGNITO_USER_CLIENT_ID"] = cognito_user_client_id
    os.environ["COGNITO_USER_CLIENT_SECRET"] = cognito_user_client_secret
    os.environ["COGNITO_TOKEN_ENDPOINT"] = cognito_token_endpoint


# Testes para a função auth_with_code


# Teste de falha ao tentar autenticar com um código inválido (código de status 400)
@patch("auth.user_auth.requests.post", return_value=RequestsMockResponse({}, 400))
def test_unsuccessful_auth_with_code(requests_post_mock):
    """Testa se a autenticação falha ao receber um código de status 400."""

    payload = {
        "grant_type": "authorization_code",
        "code": "code",
        "client_id": cognito_user_client_id,
        "redirect_uri": "redirect_uri",
    }

    # Executa a função com um código inválido
    result = auth_with_code("code", "redirect_uri")

    # Verifica se o requests.post foi chamado corretamente
    requests_post_mock.assert_called_once_with(
        cognito_token_endpoint, data=payload, headers=headers
    )

    # Como a resposta simulada tem status 400, o resultado esperado é None
    assert result is None


# Teste de sucesso ao autenticar com um código válido
@patch(
    "auth.user_auth.requests.post",
    return_value=RequestsMockResponse(
        {"access_token": "client_access_token", "expires_in": 200}, 200
    ),
)
def test_successful_auth_with_code(requests_post_mock):
    """Testa se a autenticação retorna com sucesso ao receber um código válido."""

    payload = {
        "grant_type": "authorization_code",
        "code": "code",
        "client_id": cognito_user_client_id,
        "redirect_uri": "redirect_uri",
    }

    # Executa a função com um código válido
    result = auth_with_code("code", "redirect_uri")

    # Verifica se o requests.post foi chamado corretamente
    requests_post_mock.assert_called_once_with(
        cognito_token_endpoint, data=payload, headers=headers
    )

    # O resultado esperado é um dicionário com o token e o tempo de expiração
    assert result == {"token": "client_access_token", "expires_in": 200}


# Testes para a função user_info_with_token


# Teste de sucesso ao obter informações do usuário com um token válido
@patch(
    "auth.user_auth.cognito_client.get_user",
    return_value={"ResponseMetadata": {"HTTPStatusCode": 200}},
)
def test_successful_user_info_with_token(mock_cognito_client_get_user_function):
    """Testa se as informações do usuário são retornadas corretamente com um token válido."""

    # Executa a função com um token válido
    result = user_info_with_token("access_token")

    # Verifica se o método get_user do cognito_client foi chamado com o token correto
    mock_cognito_client_get_user_function.assert_called_once_with(
        AccessToken="access_token"
    )

    # O resultado esperado é o dicionário retornado pela função simulada
    assert result == {"ResponseMetadata": {"HTTPStatusCode": 200}}


# Teste de falha ao obter informações do usuário com um token inválido (código de status 400)
@patch(
    "auth.user_auth.cognito_client.get_user",
    return_value={"ResponseMetadata": {"HTTPStatusCode": 400}},
)
def test_unsuccessful_user_info_with_token(mock_cognito_client_get_user_function):
    """Testa se a função retorna None quando falha ao obter informações do usuário com um token inválido."""

    # Executa a função com um token inválido
    result = user_info_with_token("access_token_2")

    # Verifica se o método get_user do cognito_client foi chamado com o token correto
    mock_cognito_client_get_user_function.assert_called_once_with(
        AccessToken="access_token_2"
    )

    # Como o status da resposta simulada é 400, o resultado esperado é None
    assert result is None


# Testes para a função logout_with_token


# Teste de sucesso ao realizar o logout com um token válido
@patch(
    "auth.user_auth.cognito_client.global_sign_out",
    return_value={"ResponseMetadata": {"HTTPStatusCode": 200}},
)
def test_successful_logout_with_token(mock_cognito_client_global_sign_out_function):
    """
    Testa se o logout ocorre corretamente quando um token válido é fornecido.
    """

    # Executa a função com um token válido
    result = logout_with_token("valid_access_token")

    # Verifica se o método global_sign_out do cognito_client foi chamado com o token correto
    mock_cognito_client_global_sign_out_function.assert_called_once_with(
        AccessToken="valid_access_token"
    )

    # O resultado esperado é True quando o logout é bem-sucedido
    assert result is True


# Teste de falha ao realizar o logout com um token inválido (código de status 400)
@patch(
    "auth.user_auth.cognito_client.global_sign_out",
    return_value={"ResponseMetadata": {"HTTPStatusCode": 400}},
)
def test_unsuccessful_logout_with_token(mock_cognito_client_global_sign_out_function):
    """
    Testa se a função retorna False quando falha ao realizar o logout com um token inválido.
    """

    # Executa a função com um token inválido
    result = logout_with_token("invalid_access_token")

    # Verifica se o método global_sign_out do cognito_client foi chamado com o token correto
    mock_cognito_client_global_sign_out_function.assert_called_once_with(
        AccessToken="invalid_access_token"
    )

    # Como o status da resposta simulada é 400, o resultado esperado é False
    assert result is False


# Teste para exceções inesperadas durante o logout
@patch(
    "auth.user_auth.cognito_client.global_sign_out",
    side_effect=Exception("Unexpected error occurred"),
)
def test_exception_during_logout(mock_cognito_client_global_sign_out_function):
    """
    Testa se a função lida corretamente com exceções inesperadas durante o logout.
    """

    # Executa a função que deve gerar uma exceção
    result = logout_with_token("access_token_with_error")

    # Verifica se o método global_sign_out foi chamado
    mock_cognito_client_global_sign_out_function.assert_called_once_with(
        AccessToken="access_token_with_error"
    )

    # Como ocorreu uma exceção, o resultado esperado é False
    assert result is False
