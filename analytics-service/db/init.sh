echo "Criando a tabela ToggleMasterAnalytics no DynamoDB Local..."
aws dynamodb create-table \
  --endpoint-url http://analytics-db:8000 \
  --table-name ToggleMasterAnalytics \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
  --billing-mode PAY_PER_REQUEST
echo "Tabela criada com sucesso!"