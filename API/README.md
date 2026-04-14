# API Contratos

Projeto teste com FastAPI assíncrona, SQLAlchemy 2, PostgreSQL e Alembic.

## Executar

```powershell
$env:PYTHONPATH='d:/PROJETOINI/API'
d:/PROJETOINI/API/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8007
```

## Docker Ubuntu

Este projeto agora sobe o site Vue e a API em Docker, com Nginx na frente usando o mesmo dominio.

Arquivos principais:

- `docker-compose.yml`: sobe `api` + `web` e usa sua base Postgres atual.
- `docker-compose.with-db.yml`: adiciona um Postgres em container, se voce quiser um banco novo dentro do Docker.
- `.env.production.example`: modelo de configuracao para Ubuntu.
- `.env.http.example`: modelo para primeiro deploy em HTTP, sem HTTPS.

### Primeiro deploy em HTTP

Se esta e a primeira subida, faca primeiro em HTTP para validar dominio, frontend, API e conexao com o banco atual. So depois vale a pena colocar HTTPS.

Fluxo recomendado:

```bash
cd /opt/PROJETOINI/API
cp .env.http.example .env
nano .env
docker compose up -d --build
docker compose logs -f api
docker compose logs -f web
```

Checklist desse primeiro deploy:

- O DNS do dominio ja aponta para o IP do Ubuntu.
- A porta 80 esta liberada no firewall.
- O PostgreSQL atual esta acessivel a partir do container.
- O site abre em `http://SEU_DOMINIO/`.
- O Swagger abre em `http://SEU_DOMINIO/swagger`.
- O login responde em `http://SEU_DOMINIO/api/v1/auth/login`.

### Cenario recomendado: manter sua base Postgres atual

Se voce ja tem dados no PostgreSQL, este e o caminho mais seguro. A API vai usar os registros existentes, sem precisar importar nada, desde que `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` e `DB_NAME` apontem para esse banco.

Antes da primeira subida, faca backup:

```bash
pg_dump -h 127.0.0.1 -U postgres -d Contratos > backup_contratos.sql
```

Passo a passo no Ubuntu:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker

sudo mkdir -p /opt/PROJETOINI
cd /opt/PROJETOINI
git clone REPO_DA_API API
git clone REPO_DO_FRONTEND FRONTEND
cd /opt/PROJETOINI/API
cp .env.production.example .env
nano .env
docker compose up -d --build
docker compose logs -f api
```

Estrutura esperada no servidor:

```text
/opt/PROJETOINI/
	API/
	FRONTEND/
```

Configuracao minima do `.env`:

```env
APP_DOMAIN=app.seudominio.com
VITE_API_URL=https://app.seudominio.com/api/v1
PUBLIC_API_BASE_URL=https://app.seudominio.com

DB_HOST=host.docker.internal
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=troque-esta-senha
DB_NAME=Contratos

JWT_SECRET_KEY=troque-esta-chave-forte
SECRET_ENCRYPTION_KEY=troque-esta-chave-forte
QUEPASA_HEALTH_PASSWORD=troque-esta-chave-forte
```

Modelo pronto para esse primeiro deploy: [.env.http.example](.env.http.example)

Resultado esperado:

- Site: `http://app.seudominio.com/`
- API: `http://app.seudominio.com/api/v1`
- Swagger: `http://app.seudominio.com/swagger`

### Cenario alternativo: subir um Postgres novo no Docker

Use este modo apenas se voce nao quiser reaproveitar o banco atual:

```bash
docker compose -f docker-compose.yml -f docker-compose.with-db.yml up -d --build
```

Nesse modo, o banco sobe no servico `db` e fica persistido no volume `postgres_data`.

### Observacoes importantes

- O servico `api` roda `alembic upgrade head` antes de iniciar o Uvicorn.
- Se o PostgreSQL estiver instalado no mesmo Ubuntu, fora do Docker, use `DB_HOST=host.docker.internal`.
- Se seu banco atual ja tem os dados e a estrutura esperada, a API vai ler esses dados diretamente.
- Se houver migracoes novas ainda nao aplicadas, o Alembic vai tentar aplicá-las ao subir. Por isso o backup antes da primeira subida e obrigatorio na pratica.
- O build Docker do site espera que as pastas `API` e `FRONTEND` fiquem lado a lado no servidor, como no exemplo acima.

## Frontend

O frontend deste projeto fica fora desta pasta da API, em `D:\PROJETOINI\FRONTEND`.

```powershell
Set-Location D:\PROJETOINI\FRONTEND
npm install
npm run dev -- --host=127.0.0.1 --port=5174
```

- Frontend: `http://127.0.0.1:5174/`
- API usada pelo frontend: `http://127.0.0.1:8007/api/v1`

## WhatsApp PDF

- Para enviar contrato em PDF pelo QuePasa, configure `PUBLIC_API_BASE_URL` no `.env` da API com uma URL publica da API, por exemplo: `https://api.seudominio.com`.
- `127.0.0.1`, `localhost` ou `0.0.0.0` nao funcionam para `senddocument`, porque o provedor precisa baixar o PDF a partir de fora da sua maquina.

## Swagger

- Swagger UI: `http://127.0.0.1:8007/swagger`
- OpenAPI JSON: `http://127.0.0.1:8007/openapi.json`
- ReDoc: `http://127.0.0.1:8007/redoc`

## Autenticacao JWT

- Login: `POST /api/v1/auth/login`
- Refresh: `POST /api/v1/auth/refresh`
- Usuario autenticado: `GET /api/v1/auth/me`
- Os endpoints de usuarios exigem token Bearer no Swagger.
- Apenas `admin` pode criar, alterar e excluir usuarios.
- Usuario admin seed: `ana.souza`
- Senha seed padrao: `123456`

## Reutilizacao

- A paginacao comum foi centralizada em `app/schemas/pagination.py`
- O dependency compartilhado de query params esta em `app/api/dependencies.py`

## Endpoints

- `GET /health`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `GET /api/v1/usuarios/?page=1&page_size=10&nome=Ana&ativo=true`
- `GET /api/v1/usuarios/{id}`
- `POST /api/v1/usuarios/`
- `PUT /api/v1/usuarios/{id}`
- `DELETE /api/v1/usuarios/{id}`
