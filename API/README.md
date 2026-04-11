# API Contratos

Projeto teste com FastAPI assíncrona, SQLAlchemy 2, PostgreSQL e Alembic.

## Executar

```powershell
$env:PYTHONPATH='d:/PROJETOINI/API'
d:/PROJETOINI/API/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8007
```

## Frontend

O frontend deste projeto fica fora desta pasta da API, em `D:\PROJETOINI\FRONTEND`.

```powershell
Set-Location D:\PROJETOINI\FRONTEND
npm install
npm run dev -- --host=127.0.0.1 --port=5174
```

- Frontend: `http://127.0.0.1:5174/`
- API usada pelo frontend: `http://127.0.0.1:8007/api/v1`

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
