echo "Criando a Fila de Eventos no SQS Local..."
aws sqs create-queue \
  --endpoint-url http://analytics-sqs:4566 \
  --queue-name FilaDeEventosAnalytics
echo "Fila criada com sucesso!"