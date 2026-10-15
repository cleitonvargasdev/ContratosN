# Tenant em tenants.vstec.net

Para cadastrar uma empresa e criar automaticamente seu banco, configurações,
domínio e HTTPS, consulte [Provisionamento automático](provisionamento-automatico-tenant.md).
O fluxo abaixo instala o painel; o provisionador exige a preparação adicional
do serviço no Ubuntu descrita nesse novo roteiro.

O repositorio tem raiz em `PROJETOINI` e inclui tres projetos/pastas:

```text
API/       API compartilhada e rotas administrativas /api/platform
FRONTEND/  Frontend das empresas
TENANT/    Frontend administrativo Tenant
```

O painel usa o banco separado `tenant_registry`, com `cad_usuario`,
`tenant_admin_sessions`, `tenants` e `tenant_domains`. Nao ha sincronizacao de
usuarios administrativos com os bancos das empresas. O banco local criado no
desenvolvimento nao e enviado pelo Git; inicialize tambem o banco no Ubuntu.

## Git

Envie a pasta `TENANT` e as alteracoes da `API` no mesmo repositorio. Nao envie
`node_modules`, `dist`, arquivos `.env` nem backups de banco. `TENANT/.gitignore`
ja exclui as dependencias, o build e `.env.local`. O `package-lock.json` deve
ser versionado para o build reproduzivel com `npm ci`.

## Docker no Ubuntu

Execute a partir da pasta API do mesmo checkout/projeto Compose ja utilizado
pela instalacao. O caminho documentado para este servidor e:

```bash
cd /var/www/apicontratos/ContratosN/API
git pull
docker compose -f docker-compose.yml -f docker-compose.tenant.yml build api tenant-web
docker compose -f docker-compose.yml -f docker-compose.tenant.yml run --rm --no-deps --entrypoint python api -m scripts.init_tenant_admin
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d api tenant-web
```

Se a instalacao usa arquivos Compose adicionais (por exemplo o servico `db`),
preserve esses mesmos arquivos/opcoes e acrescente `-f docker-compose.tenant.yml`.
O PostgreSQL deve estar disponivel para o inicializador. A conta configurada em
`API/.env` precisa poder criar o registro, ou o banco deve ser criado previamente.

O inicializador usa `TENANT_REGISTRY_DB_NAME` (padrao `tenant_registry`) e cria
`ADMIN` com senha inicial `Admin` apenas se `cad_usuario` estiver vazia. Nao
redefine senhas em atualizacoes. Entre no painel e altere a senha no seu perfil.

O servico `tenant-web` atende apenas em `127.0.0.1:8081` do Ubuntu; o frontend
existente continua na porta 8080. O proxy interno envia `/api/platform/` para
`api:8007`, preservando o caminho. A API deve ter sido reconstruida para incluir
as rotas administrativas. Use os mesmos arquivos Compose nas atualizacoes.

## Dominio e HTTPS

Use `docker/tenant-ubuntu.nginx.example` como virtual host do dominio
`tenants.vstec.net` no Nginx do Ubuntu, encaminhando para `127.0.0.1:8081`.
Se ja utiliza outro proxy (Nginx Proxy Manager, Traefik etc.), configure nele
esse dominio e destino. Ative o certificado HTTPS pelo mecanismo utilizado no
servidor antes de entrar com credenciais. O exemplo incluido cobre somente HTTP.

Como frontend e API sao acessados pelo mesmo dominio, nao e necessario configurar
CORS para outra origem. O dominio administrativo nao deve ser cadastrado como
dominio de CV/BC: ele serve o painel, nao uma empresa. Tambem nao precisa ser
adicionado a `TENANT_API_HOSTS`, pois as rotas administrativas tem autenticacao
propria e nao passam pela resolucao de tenant.

## Conferencia

```bash
docker compose -f docker-compose.yml -f docker-compose.tenant.yml ps
curl -I http://127.0.0.1:8081/
curl -i http://127.0.0.1:8081/api/platform/tenants
```

O frontend deve responder 200 e a listagem sem login deve responder 401. Depois
acesse `https://tenants.vstec.net`, entre e confira usuarios e tenants.

O cadastro de empresas continua exigindo os respectivos bancos e variaveis
`TENANT_<CODIGO>_DATABASE_URL` e `TENANT_<CODIGO>_WEBHOOK_SECRET` na API.
No modo de vincular banco existente, o painel cadastra empresas, dominios e
ativacoes. O modo automático cria o banco e configura o site após instalar o
provisionador. DNS permanece uma etapa externa, anterior ao cadastro.

Estes arquivos preparam a implantacao; nao confirmam DNS, certificado, build
Docker ou publicacao no servidor. Validar essas etapas no Ubuntu.
