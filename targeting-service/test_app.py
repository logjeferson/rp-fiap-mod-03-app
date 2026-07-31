import os
import pytest
import psycopg2
from unittest.mock import patch, MagicMock

# 1. Configura variáveis fakes ANTES da importação
os.environ['DATABASE_URL'] = 'postgres://fake_user:fake_pass@localhost:5432/fake_db'
os.environ['AUTH_SERVICE_URL'] = 'http://fake-auth-service.local'

# 2. Mock do Pool de Conexões do PostgreSQL
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
    """Mocka o auth-service para retornar 200 OK (Autorizado) por padrão."""
    with patch('app.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        yield mock_get

@pytest.fixture
def mock_db():
    """Mocka o pool, a conexão e o cursor do PostgreSQL."""
    with patch('app.pool') as mock_pool:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        yield {'pool': mock_pool, 'conn': mock_conn, 'cursor': mock_cursor}


# --- Testes Unitários ---

def test_health_check(client):
    """Teste 1: Endpoint público de health"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_create_rule_success(client, mock_auth, mock_db):
    """Teste 2: Criação de regra com sucesso"""
    # Simula o retorno do banco de dados (RETURNING *)
    mock_db['cursor'].fetchone.return_value = {
        "flag_name": "nova_home", 
        "rules": {"country": "BR", "device": "mobile"}, 
        "is_enabled": True
    }
    
    payload = {
        "flag_name": "nova_home",
        "rules": {"country": "BR", "device": "mobile"},
        "is_enabled": True
    }
    
    response = client.post('/rules', json=payload, headers={"Authorization": "Bearer token"})
    
    assert response.status_code == 201
    assert response.json["flag_name"] == "nova_home"
    assert response.json["rules"]["country"] == "BR"
    
    # Verifica chamadas ao banco
    mock_db['cursor'].execute.assert_called_once()
    sql_query = mock_db['cursor'].execute.call_args[0][0]
    assert "INSERT INTO targeting_rules" in sql_query
    mock_db['conn'].commit.assert_called_once()


def test_create_rule_missing_fields(client, mock_auth, mock_db):
    """Teste 3: Tentar criar regra sem o objeto JSON 'rules'"""
    payload = {"flag_name": "nova_home"} # Falta o 'rules'
    
    response = client.post('/rules', json=payload, headers={"Authorization": "Bearer token"})
    
    assert response.status_code == 400
    assert "obrigatorios" in response.json["error"]
    mock_db['pool'].getconn.assert_not_called() # Não deve nem tocar no banco


def test_create_rule_duplicate(client, mock_auth, mock_db):
    """Teste 4: Tentar criar uma regra para uma flag que já tem regra (409 Conflict)"""
    # Simula um erro de chave duplicada disparado pelo psycopg2
    mock_db['cursor'].execute.side_effect = psycopg2.IntegrityError("Unique violation")
    
    payload = {"flag_name": "flag_existente", "rules": {}}
    
    response = client.post('/rules', json=payload, headers={"Authorization": "Bearer token"})
    
    assert response.status_code == 409
    assert response.json["error"] == "Regra para a flag 'flag_existente' ja existe"
    mock_db['conn'].rollback.assert_called_once() # Garante que fez rollback


def test_get_rule_success(client, mock_auth, mock_db):
    """Teste 5: Buscar regra existente"""
    mock_db['cursor'].fetchone.return_value = {
        "flag_name": "botao_azul", 
        "rules": {"beta_users": True}
    }
    
    response = client.get('/rules/botao_azul', headers={"Authorization": "Bearer token"})
    
    assert response.status_code == 200
    assert response.json["rules"]["beta_users"] is True


def test_update_rule_success(client, mock_auth, mock_db):
    """Teste 6: Atualizar as regras de uma flag"""
    # rowcount > 0 indica que encontrou e atualizou a linha
    mock_db['cursor'].rowcount = 1
    mock_db['cursor'].fetchone.return_value = {
        "flag_name": "botao_azul",
        "rules": {"beta_users": False}, # Regra alterada
        "is_enabled": False
    }
    
    payload = {"rules": {"beta_users": False}, "is_enabled": False}
    response = client.put('/rules/botao_azul', json=payload, headers={"Authorization": "Bearer token"})
    
    assert response.status_code == 200
    assert response.json["is_enabled"] is False
    
    # Verifica se a query de UPDATE foi montada
    sql_query = mock_db['cursor'].execute.call_args[0][0]
    assert "UPDATE targeting_rules SET" in sql_query
    mock_db['conn'].commit.assert_called_once()


def test_delete_rule_success(client, mock_auth, mock_db):
    """Teste 7: Deletar uma regra"""
    mock_db['cursor'].rowcount = 1 # Simula que 1 linha foi deletada
    
    response = client.delete('/rules/botao_azul', headers={"Authorization": "Bearer token"})
    
    assert response.status_code == 204 # No Content
    mock_db['conn'].commit.assert_called_once()


def test_delete_rule_not_found(client, mock_auth, mock_db):
    """Teste 8: Tentar deletar uma regra que não existe"""
    mock_db['cursor'].rowcount = 0 # Simula que nenhuma linha foi afetada
    
    response = client.delete('/rules/flag_fantasma', headers={"Authorization": "Bearer token"})
    
    assert response.status_code == 404
    assert response.json["error"] == "Regra nao encontrada"