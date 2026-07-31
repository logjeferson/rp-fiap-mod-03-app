echo "Criando a Fila de Eventos no SQS Local..."
aws sqs create-queue \
  --endpoint-url http://evaluation-sqs:4565 \
  --queue-name FilaDeEventosEvaluation
echo "Fila criada com sucesso!"