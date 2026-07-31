# Microsserviço de Aplicação - Plataforma Cloud

> 🎓 **Projeto Acadêmico - FIAP**
> Este repositório é um projeto de estudos desenvolvido para o curso de **Pós-graduação em DevOps e Arquitetura Cloud da FIAP**. A aplicação possui fins estritamente educacionais e atende a um cenário técnico específico de microsserviços proposto em sala de aula.

Este repositório contém o código-fonte de um dos microsserviços da arquitetura (ex: `analytics-service`, `flag-service` ou `targeting-service`), construído em **Python (Flask)**, projetado para alta escalabilidade, integração com bancos de dados e comunicação segura entre serviços na nuvem AWS.

## 🛠️ Stack Tecnológica

*   **Linguagem & Framework:** Python 3.x com Flask (APIs RESTful).
*   **Persistência / Dados:** 
    *   PostgreSQL com gerenciamento de pool de conexões (`psycopg2` e `SimpleConnectionPool`).
    *   Amazon DynamoDB e Amazon SQS via AWS Boto3 (dependendo do microsserviço).
*   **Autenticação & Segurança:** Middleware customizado com validação de tokens via requisições HTTP (`requests`) integrado a um serviço de autenticação (`auth-service`).
*   **Qualidade e Testes:** Suítes de testes unitários utilizando `pytest` e `unittest.mock` para isolamento de dependências externas.

## 🌿 Padrão de Desenvolvimento e Estratégia de Branches

O desenvolvimento segue o fluxo de integração contínua alinhado com o modelo GitFlow:
*   `main` / `master`: Branch de produção, protegida contra pushes diretos.
*   `develop` / `feature/*`: Branches de desenvolvimento e novas funcionalidades que disparam os pipelines automatizados.

## 🔐 Segurança e Autenticação

*   **Validação de Acesso:** Todas as rotas protegidas exigem o header `Authorization`, validado via middleware contra o serviço centralizado de auth.
*   **Tratamento de Falhas:** Mecanismos robustos de tratamento para indisponibilidade ou timeout (`504 Gateway Timeout`, `503 Service Unavailable`).

## 🚀 Integração Contínua (CI/CD)

O pipeline executado via **GitHub Actions** assegura a qualidade do código antes do empacotamento:
1.  **Análise Estática (SAST):** Inspeção de código via SonarCloud.
2.  **Análise de Vulnerabilidades (SCA):** Scans de dependências e arquivos com o Trivy.
3.  **Testes Automatizados:** Execução do `pytest` com mocks de banco, SQS e auth para evitar dependências de infraestrutura externa no build.
4.  **Containerização:** Build e push da imagem Docker imutável para o **Amazon ECR**, tagueada utilizando o hash do commit (`${{ github.sha }}`).

## 🛠️ Como Executar Localmente

### Pré-requisitos
*   Python 3.10+ instalado.
*   Ambiente virtual configurado (`venv`).

### Passo a Passo

```bash
# 1. Clonar o repositório e entrar na pasta do serviço
cd <nome-do-microsservico>

# 2. Criar e ativar o ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# 3. Instalar as dependências
pip install -r requirements.txt
pip install pytest

# 4. Configurar as variáveis de ambiente locais (criar um arquivo .env)
# DATABASE_URL=postgres://...
# AUTH_SERVICE_URL=http://...

# 5. Executar os testes unitários
pytest

# 6. Rodar a aplicação localmente
python app.py
