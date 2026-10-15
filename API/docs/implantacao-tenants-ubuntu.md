# Implantacao dos tenants CV e BC no Ubuntu

## Resultado planejado

| Dominio | Codigo no aplicativo | Banco |
|---|---|---|
| cvfinanceiro.vstec.net | cv | cv_financeiro |
| bcfinanceiro.vstec.net | bc | bc_financeiro |

Os dois bancos recebem uma copia completa da mesma fotografia do banco
`Contratos`. O original permanece intacto. Depois da copia, alteracoes em uma
empresa nao se propagam para a outra.

O banco administrativo `tenant_registry` guarda empresas, dominios, referencias
para conexoes e flags de ativacao. Nao guarda contratos nem senhas de banco.
As URLs de conexao ficam em variaveis de ambiente do servidor.

Este roteiro foi preparado no desenvolvimento. Ainda e necessario executar e
validar a implantacao no Ubuntu. O caminho registrado em `ATUALIZAR.txt` e
`/var/www/apicontratos/ContratosN/API`.

## 1. Conferir o servidor antes de alterar

No Ubuntu, no diretorio da API, execute:

```bash
cd /var/www/apicontratos/ContratosN/API
docker compose exec -T api python -c "from app.core.config import settings; print('Banco:', settings.db_name); print('Host:', settings.db_host); print('Porta:', settings.db_port)"
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
```

Esses comandos nao exibem senhas. O projeto local aponta para `Contratos` em
`localhost:5432`; os exemplos de producao usam `host.docker.internal` para
PostgreSQL instalado diretamente no Ubuntu. Confirme pelo retorno real.

Para identificar PostgreSQL como servico do Ubuntu:

```bash
systemctl is-active postgresql
pg_lsclusters
```

Para copiar pelo host, tenha `psql`, `pg_dump`, `pg_restore` e `createdb`
instalados. Use clientes da mesma versao principal do servidor ou mais novos.
O usuario da conexao precisa ler a origem e criar os bancos novos.
Se PostgreSQL estiver em container, confirme a porta publicada antes de usar
`127.0.0.1`; nao presuma que o endereco interno `db` funciona no host Ubuntu.

## 2. Copia definitiva dos bancos

Disponibilize os arquivos deste trabalho no servidor. Antes da copia definitiva,
pare as escritas: API antiga, aplicativos, integracoes e outros processos que
escrevam em `Contratos`. O script usa um unico dump consistente para as duas
restauracoes; escritas posteriores ao dump nao sao sincronizadas.

```bash
docker compose stop api
export PGHOST=127.0.0.1
export PGPORT=5432
export PGUSER=postgres
read -rsp 'Senha do PostgreSQL: ' PGPASSWORD
echo
export PGPASSWORD
SOURCE_DB=Contratos bash scripts/clone_tenant_databases.sh
unset PGPASSWORD
```

Adapte host/porta/usuario aos resultados da etapa anterior. Tambem e possivel
usar `PGPASSFILE` com permissao 600. Nao cole senhas em mensagens ou comandos.

O script:

- recusa qualquer destino que ja exista e recusa nomes iguais;
- salva um backup de acesso restrito em `tenant-backups/`;
- restaura todos os dados e estruturas em `cv_financeiro` e `bc_financeiro`;
- desliga apenas os agendamentos de score e WhatsApp nas copias;
- cria `tenant_registry` vazio;
- compara as contagens de todas as tabelas publicas com a origem.

Usuarios, senhas de login, contratos, recebimentos, comissoes e configuracoes
existentes sao copiados. As permissoes/owners PostgreSQL do dump nao sao
restaurados: o usuario que executa a restauracao passa a ser o proprietario.
Caso use contas PostgreSQL dedicadas por empresa, conceda acesso e propriedade
adequados antes de executar as migracoes com essas contas.

Em caso de falha, o script deixa o backup e eventuais bancos parcialmente
criados para inspecao. Nao apaga bancos nem substitui automaticamente destinos.
Nao ative o sistema sem concluir a restauracao e a verificacao.

## 3. Configurar a API e o frontend

Mantenha `JWT_SECRET_KEY` e `SECRET_ENCRYPTION_KEY` existentes: dados copiados
podem depender dessas chaves para descriptografar configuracoes.
Mantenha `DB_NAME=Contratos`; a aplicacao usa esse nome como protecao para nao
apontar um tenant acidentalmente para a origem. `DB_HOST`, `DB_PORT`, `DB_USER`
e `DB_PASSWORD` tambem sao usados para acessar o registro central.

Adicione/ajuste no `.env` do Ubuntu, sem versionar credenciais:

```dotenv
TENANCY_ENABLED=true
TENANT_REGISTRY_DB_NAME=tenant_registry
TENANT_API_HOSTS=

APP_DOMAIN="cvfinanceiro.vstec.net bcfinanceiro.vstec.net"
VITE_API_URL=/api/v1
CORS_ALLOW_ORIGINS=https://cvfinanceiro.vstec.net,https://bcfinanceiro.vstec.net

TENANT_CV_DATABASE_URL='postgresql+asyncpg://USUARIO:SENHA_CODIFICADA@host.docker.internal:5432/cv_financeiro'
TENANT_BC_DATABASE_URL='postgresql+asyncpg://USUARIO:SENHA_CODIFICADA@host.docker.internal:5432/bc_financeiro'
TENANT_CV_WEBHOOK_SECRET=SEGREDO_ALEATORIO_CV_COM_32_OU_MAIS_CARACTERES
TENANT_BC_WEBHOOK_SECRET=OUTRO_SEGREDO_ALEATORIO_BC_COM_32_OU_MAIS_CARACTERES
```

As URLs devem ser acessiveis de dentro do container da API. Use aspas simples
no `.env` para evitar interpolacao de `$`. Caracteres especiais do usuario e
da senha na URL precisam de percent-encoding. Nao use literalmente os valores
de exemplo. Use segredos distintos para os dois webhooks.

Se o PostgreSQL estiver no servico `db` do Compose, use esse host em vez de
`host.docker.internal`. O registro central e as duas copias precisam existir
na instancia acessivel pela API.

O frontend usa `/api/v1` no proprio dominio. Isso e necessario para a BC nao
enviar o login ao dominio da CV. Os WebSockets tambem seguem o dominio atual.
O build local continua usando o padrao `127.0.0.1:8007` quando `VITE_API_URL`
nao estiver definido.

O build Docker da API exclui `.env` e `.env.local`; a configuracao em producao
entra pelo `env_file` do Compose. Assim, configuracoes locais nao substituem
as do Ubuntu dentro da imagem.

## 4. Cadastrar as empresas e migrar as copias

Primeiro construa a imagem sem iniciar a API. Os comandos administrativos
ignoram o entrypoint para poder inicializar o registro antes das migracoes.

```bash
docker compose build api
docker compose run --rm --no-deps --entrypoint python api -m scripts.manage_tenants init
docker compose run --rm --no-deps --entrypoint python api -m scripts.manage_tenants register --code cv --domain cvfinanceiro.vstec.net --database-env TENANT_CV_DATABASE_URL --webhook-env TENANT_CV_WEBHOOK_SECRET
docker compose run --rm --no-deps --entrypoint python api -m scripts.manage_tenants register --code bc --domain bcfinanceiro.vstec.net --database-env TENANT_BC_DATABASE_URL --webhook-env TENANT_BC_WEBHOOK_SECRET
docker compose run --rm --no-deps --entrypoint python api -m scripts.manage_tenants list
docker compose run --rm --no-deps --entrypoint python api -m scripts.migrate_databases
```

Os tenants sao criados ativos para login, com `automations_enabled=false` e
`whatsapp_enabled=false`. O registro so guarda nomes de variaveis de ambiente.
O cadastro recusa empresas/dominos existentes e bancos compartilhados.

As 49 migracoes atuais de negocio continuam sendo aplicadas a cada copia,
com uma tabela `alembic_version` em cada banco. As tabelas administrativas
pertencem a um metadata separado e sao inicializadas pelo comando `init`.
No modo tenant, executar `alembic upgrade head` diretamente e bloqueado: use
`python -m scripts.migrate_databases`. Se qualquer migracao falhar, a API nao
deve ser iniciada. Bancos anteriores podem ja ter migrado; o Alembic retoma
do ponto registrado ao executar novamente.

## 5. Dominios e entrada em operacao

Os dois dominios devem apontar para o servidor. O proxy HTTPS externo precisa
ter certificados para ambos e encaminhar o Host original para o container web
na porta 8080. O Nginx interno repassa o Host para a API. A API ignora
`X-Forwarded-Host` e bloqueia hosts nao cadastrados.

```bash
docker compose up -d --build api web
docker compose logs --tail=100 api
```

Entre separadamente em cada dominio e confira clientes, contratos, saldos e
permissoes. Em uma conta de teste, confirme que uma alteracao feita na CV nao
aparece na BC. Logins existentes continuam validos nos dois bancos copiados.

Tokens emitidos antes da ativacao nao possuem `tenant_id` e deixam de ser
aceitos; faca login novamente. Chaves de API copiadas tambem precisam ser
regeneradas por empresa, pois o hash agora inclui o tenant. Um token da CV
usado no dominio BC e recusado, inclusive em refresh, PDF e WebSocket.

## 6. Aplicativo e chaves de API

O APK nao esta neste repositorio. O contrato de login da API foi adaptado:
`POST /api/v1/auth/login`, formulario `application/x-www-form-urlencoded`,
campos `username`, `password` e `company_code` (`cv` ou `bc`).

O app pode escolher o dominio correspondente a empresa. Se usar um dominio
unico da API, cadastre esse host em `TENANT_API_HOSTS` e configure DNS/proxy/TLS
para ele. Somente esses hosts neutros aceitam resolver a empresa pelo codigo
do login e, depois, pelo tenant do JWT. Nao inclua os dominios das empresas
como hosts neutros. Em hosts neutros, chaves de API usam `X-Company-Code`
junto com `X-API-Key`; nos dominios das empresas basta a chave.

O refresh recebe o JSON existente com `refresh_token`; a empresa vem desse
token assinado. Nenhum cliente informa nome do banco ou URL de conexao.

## 7. WhatsApp e rotinas automaticas

Como os dados foram copiados integralmente, telefones e configuracoes antigas
tambem foram copiados. Antes de ativar, configure em Parametros a sessao/token
do QuePasa correspondente a cada empresa. Use sessoes distintas. A API nao
preenche credenciais ausentes de tenants com o token global do ambiente.

O webhook de cada empresa deve apontar para seu proprio dominio:

```text
https://cvfinanceiro.vstec.net/webhooks/webhook?key=SEGREDO_CV
https://bcfinanceiro.vstec.net/webhooks/webhook?key=SEGREDO_BC
```

A tela de conexao verifica automaticamente esse cadastro quando o WhatsApp
esta conectado, inclusive depois da leitura do QR code e em Atualizar status.
A API consulta `GET /webhook` no endereco `QUEPASA_APIWPP_URL`, usando somente
o `X-QUEPASA-TOKEN` da empresa. Se a URL completa nao estiver na lista
`webhooks`, cadastra com `POST /api/webhook` e consulta novamente para confirmar.
O segredo e lido do ambiente; nao e devolvido para a tela nem registrado em logs.
Outros webhooks existentes sao preservados, inclusive URLs antigas: revise-os
no provedor ao migrar dominios ou trocar segredos para evitar entregas obsoletas.

Se a consulta ou o cadastro falhar, o WhatsApp continua mostrando seu estado
real de conexao, mas a mensagem informa que o recebimento do chatbot esta
pendente. Atualizar status tenta novamente. `webhook_ready` na resposta vale
`true` quando confirmado, `false` quando pendente, ou `null` quando nao foi
verificado (desconectado ou modo legado). Nao e necessario ativar agendamentos.
O QR code nao aguarda chamadas de webhook, preservando seu tempo de validade.
A verificacao do webhook tem um limite total de 5 segundos, incluindo espera
por consultas concorrentes. Ao exceder esse prazo, o status da conexao e
devolvido normalmente com o chatbot pendente; Atualizar status tenta novamente.

Se o provedor permitir, envie o segredo em `X-Webhook-Secret` e omita `key` da
URL. O proxy externo tambem deve omitir query strings desses acessos dos logs.
O Nginx interno nao registra acessos a `/webhooks/`, e o Compose desliga o log
de acessos do Uvicorn para nao registrar esses segredos.

Depois de revisar as configuracoes, habilite uma empresa por vez:

```bash
docker compose run --rm --no-deps --entrypoint python api -m scripts.manage_tenants set cv whatsapp_enabled on
docker compose restart api
```

Teste o status, QR code e uma mensagem controlada. Repita para BC com a sessao
propria. Para liberar os agendamentos, configure-os na tela de Parametros e
ative `automations_enabled` no cadastro da empresa:

```bash
docker compose run --rm --no-deps --entrypoint python api -m scripts.manage_tenants set cv automations_enabled on
docker compose restart api
```

O scheduler abre uma sessao separada para cada tenant; uma falha nao impede a
rotina dos demais. Use apenas um processo/replica da API nesta versao: os
schedulers e brokers de notificacao ainda sao locais ao processo. Escalar
horizontalmente requer coordenacao das rotinas e um broker compartilhado.

## Suspensao e retorno ao modo anterior

```bash
docker compose run --rm --no-deps --entrypoint python api -m scripts.manage_tenants set bc active off
docker compose restart api
```

Novas requisicoes consultam o estado atual no registro. O restart encerra
WebSockets antigos e recria pools apos mudancas administrativas ou de conexao.

Para retornar a base original, pare a API, defina `TENANCY_ENABLED=false`,
mantenha os `DB_*` originais e suba novamente. Isso nao transfere dados que ja
tenham sido escritos nas copias. Avalie esses dados antes de um retorno apos
entrada em producao. O original e o backup continuam disponiveis.

## Verificacao feita no desenvolvimento

Testes automatizados cobrem roteamento por dominio/codigo, bloqueio entre
empresas, refresh, tokens antigos e expirados, PDF, WebSocket, notificacoes,
chaves de API, autenticacao do webhook, contexto concorrente e rotinas por
empresa. Bancos SQLite independentes verificam leituras/escritas com IDs iguais.

Tambem foi executado um teste com PostgreSQL 15 temporario: aplica as 49
migracoes em uma base de teste, executa o script real de clonagem para dois
bancos, confere contagens e sequencias, verifica os agendamentos desativados
nas copias e comprova que a origem permanece intacta. O teste tambem confirma
que uma segunda execucao recusa sobrescrever os destinos.

Para repetir esse teste isolado, defina `RUN_POSTGRES_INTEGRATION=1`,
`POSTGRES_BIN` (diretorio com initdb/pg_ctl/psql) e `BASH_BIN` (executavel bash),
e execute `python -m pytest tests/test_tenant_postgres.py`. Ele cria e encerra
uma instancia temporaria em porta local livre, com senha aleatoria.
O build TypeScript/Vite tambem foi validado. A instalacao real no Ubuntu ainda
precisa passar pelas conferencias deste roteiro.
