import os
import pytest
from unittest.mock import patch, MagicMock

# 1. Configura variáveis de ambiente fakes ANTES de importar a aplicação.
os.environ['DATABASE_URL'] = 'postgres://fake_user:fake_pass@localhost:5432/fake_db'
os.environ['AUTH_SERVICE_URL'] = 'http://fake-auth-service.local'

# 2. Mockamos o SimpleConnectionPool ANTES de importar o app.
# Isso impede que a aplicação tente conectar em um banco real durante o import.
with patch('psycopg2.pool.SimpleConnectionPool'):
    import app


# --- Fixtures ---

@pytest.fixture
def client():
    """Cria um cliente de teste do Flask."""
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

@pytest.fixture
def mock_auth():
    """Mocka a chamada HTTP do middleware de autenticação (requests.get)."""
    with patch('app.requests.get') as mock_get:
        # Por padrão, simula que o auth-service retornou 200 OK (Chave Válida)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        yield mock_get

@pytest.fixture
def mock_db():
    """Mocka o pool, a conexão e o cursor do banco de dados PostgreSQL."""
    with patch('app.pool') as mock_pool:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Configura o comportamento encadeado: pool -> conn -> cursor
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Retorna o cursor e a conexão para podermos alterar os retornos em cada teste
        yield {'pool': mock_pool, 'conn': mock_conn, 'cursor': mock_cursor}


# --- Testes Unitários ---

def test_health_check(client):
    """Teste 1: Rota pública (não exige auth nem banco)"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_auth_middleware_missing_header(client):
    """Teste 2: Tentativa de acessar rota protegida sem header de Authorization"""
    response = client.get('/flags')
    assert response.status_code == 401
    assert response.json == {"error": "Authorization header obrigatorio"}


def test_auth_middleware_invalid_token(client, mock_auth):
    """Teste 3: Tentativa de acesso com token rejeitado pelo auth-service"""
    # Altera o mock para simular que o auth-service retornou 401 (Não autorizado)
    mock_auth.return_value.status_code = 401
    
    response = client.get('/flags', headers={"Authorization": "Bearer token_invalido"})
    assert response.status_code == 401
    assert response.json == {"error": "Chave de API invalida"}


def test_create_flag_success(client, mock_auth, mock_db):
    """Teste 4: Criação de uma flag com sucesso (Caminho Feliz)"""
    # Prepara o retorno falso do banco de dados (o que o 'RETURNING *' devolveria)
    mock_flag_retorno = {
        "name": "nova_feature", 
        "description": "Teste", 
        "is_enabled": True
    }
    mock_db['cursor'].fetchone.return_value = mock_flag_retorno
    
    payload = {"name": "nova_feature", "description": "Teste", "is_enabled": True}
    
    response = client.post('/flags', json=payload, headers={"Authorization": "Bearer token_valido"})
    
    assert response.status_code == 201
    assert response.json["name"] == "nova_feature"
    
    # Verifica se a query de INSERT foi executada
    mock_db['cursor'].execute.assert_called_once()
    assert "INSERT INTO flags" in mock_db['cursor'].execute.call_args[0][0]
    
    # Verifica se o commit foi chamado e a conexão devolvida ao pool
    mock_db['conn'].commit.assert_called_once()
    mock_db['pool'].putconn.assert_called_once_with(mock_db['conn'])


def test_create_flag_missing_name(client, mock_auth, mock_db):
    """Teste 5: Tentar criar flag sem o campo obrigatório 'name'"""
    payload = {"description": "Falta o nome"}
    
    response = client.post('/flags', json=payload, headers={"Authorization": "Bearer token_valido"})
    
    assert response.status_code == 400
    assert response.json == {"error": "'name' e obrigatorio"}
    # Garante que o banco nem foi tocado
    mock_db['pool'].getconn.assert_not_called()


def test_get_flags_success(client, mock_auth, mock_db):
    """Teste 6: Listagem de todas as flags"""
    mock_flags = [
        {"name": "flag1", "is_enabled": True},
        {"name": "flag2", "is_enabled": False}
    ]
    # 'fetchall' devolve uma lista
    mock_db['cursor'].fetchall.return_value = mock_flags
    
    response = client.get('/flags', headers={"Authorization": "Bearer token_valido"})
    
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]["name"] == "flag1"


def test_get_flag_not_found(client, mock_auth, mock_db):
    """Teste 7: Busca por uma flag que não existe"""
    # Se o 'fetchone' retornar None, a flag não foi encontrada
    mock_db['cursor'].fetchone.return_value = None
    
    response = client.get('/flags/flag_inexistente', headers={"Authorization": "Bearer token_valido"})
    
    assert response.status_code == 404
    assert response.json == {"error": "Flag nao encontrada"}