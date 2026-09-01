import os
import json
import pytest
from unittest.mock import patch

os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_SQS_URL"] = (
    "https://sqs.us-east-1.amazonaws.com/cache-cluster-01/EventQueue"
)
os.environ["AWS_DYNAMODB_TABLE"] = "ToggleMasterAnalytics"

with patch("boto3.Session"), patch("threading.Thread"):
    import app

# --- Fixtures ---


@pytest.fixture
def client():
    """Cria um cliente de teste do Flask para testarmos as rotas da API."""
    app.app.config["TESTING"] = True
    with app.app.test_client() as client:
        yield client


# --- Testes Unitários ---


def test_health_check(client):
    """Teste 1: Verifica se o servidor Flask está rodando e respondendo no /health"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


@patch("app.dynamodb_client")
@patch("app.sqs_client")
def test_process_message_success(mock_sqs, mock_dynamo):
    """Teste 2: Verifica o caminho feliz de processar uma mensagem válida"""

    # Prepara uma mensagem SQS simulada
    fake_body = {
        "user_id": "usr-999",
        "flag_name": "nova_home_page",
        "result": True,
        "timestamp": "2026-07-31T12:00:00Z",
    }

    fake_message = {
        "MessageId": "msg-id-12345",
        "ReceiptHandle": "receipt-handle-abcde",
        "Body": json.dumps(fake_body),
    }

    # Executa a função do seu código
    app.process_message(fake_message)

    # VALIDAÇÃO 1: O DynamoDB foi chamado para inserir o item?
    mock_dynamo.put_item.assert_called_once()

    # Inspeciona os argumentos que foram passados para o DynamoDB
    call_args = mock_dynamo.put_item.call_args[1]
    assert call_args["TableName"] == "ToggleMasterAnalytics"
    assert call_args["Item"]["user_id"]["S"] == "usr-999"
    assert call_args["Item"]["flag_name"]["S"] == "nova_home_page"
    assert call_args["Item"]["result"]["BOOL"] is True

    # VALIDAÇÃO 2: A mensagem foi deletada da fila SQS após o sucesso?
    mock_sqs.delete_message.assert_called_once_with(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/cache-cluster-01/EventQueue",
        ReceiptHandle="receipt-handle-abcde",
    )

@patch("app.dynamodb_client")
@patch("app.sqs_client")
def test_process_message_invalid_json(mock_sqs, mock_dynamo):
    """Teste 3: Verifica se a aplicação resiste a uma mensagem com JSON quebrado (Poison Pill)"""

    fake_message = {
        "MessageId": "msg-id-erro-001",
        "ReceiptHandle": "receipt-handle-erro",
        "Body": "isso-nao-e-um-json-valido-vai-quebrar-o-loads",
    }

    # A função deve capturar o erro e não deve dar "crash" (exception não tratada)
    app.process_message(fake_message)

    # VALIDAÇÃO 1: Como o JSON era inválido, NÃO devemos tentar salvar no banco
    mock_dynamo.put_item.assert_not_called()

    # VALIDAÇÃO 2: A mensagem NÃO deve ser apagada da fila para que caia em uma DLQ depois
    mock_sqs.delete_message.assert_not_called()
