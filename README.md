# Forge — diário de treino

Aplicação pessoal em Django para registrar exercícios, técnicas avançadas e treinos, com análise diária, semanal e mensal em tabela e gráfico de linha.

## Arquitetura

O projeto usa MVC do Django (templates fazem o papel de View) organizado por contexto e feature:

```text
contexts/
├── manager/features/authentication/   # cadastro, login, logout e sessão
└── academia/features/
    ├── catalog/                       # exercícios e técnicas avançadas
    ├── training/                      # registros de treino
    ├── analytics/                     # painel e resumo de análise
    └── analytics_graphql/             # API GraphQL analítica e documentação
```

A API de análise está disponível em `/api/analytics/graphql/`. O catálogo completo de consultas, campos, funções e exemplos fica em `contexts/academia/features/analytics_graphql/README.md`.

Cada feature concentra seus próprios `forms`, `views`, `urls` e serviços. `contexts/academia/models.py` apenas expõe os modelos para o mecanismo de descoberta do Django.

## Executar com Docker

```bash
docker build -t forge .
docker volume create forge-data
docker run --name forge \
  --publish 127.0.0.1:8000:8000 \
  --env DEBUG=true \
  --env DATABASE_PATH=/data/forge.sqlite3 \
  --volume forge-data:/data \
  forge
```

No PowerShell, o mesmo comando pode ser escrito em uma única linha. A porta é publicada somente na interface local, e a aplicação fica disponível em `http://localhost:8000`. Migrações e arquivos estáticos são preparados automaticamente ao iniciar o container.

## Deploy no Railway

1. Envie o repositório ao GitHub e crie um serviço no Railway a partir dele. O Railway detectará o `Dockerfile` e construirá somente essa imagem; não há Docker Compose.
2. Crie um **Volume** e monte-o em `/data`. SQLite sem Volume é efêmero e pode perder dados em redeploys.
3. Configure as variáveis:

```text
DATABASE_PATH=/data/forge.sqlite3
SECRET_KEY=<uma chave longa e aleatória>
DEBUG=false
ALLOWED_HOSTS=.railway.app
CSRF_TRUSTED_ORIGINS=https://*.railway.app
```

4. Gere um domínio no Railway. O `railway.json` seleciona o Dockerfile e configura o health check `/health/`. O `docker-entrypoint.sh` aplica migrações, coleta os arquivos estáticos e inicia o Gunicorn automaticamente.

Como a aplicação é de uso pessoal, o formulário de cadastro aceita somente a primeira conta. Depois disso, a própria rota redireciona para o login e nenhum outro usuário pode se cadastrar.

## Testes

```bash
python manage.py check
python manage.py test
```
