# Processos Ubuntu

Registro operacional da plataforma Contratos e do painel Tenant.

Atualizado em **15/10/2026**. A instalação do painel `tenants.vstec.net`, seguindo os comandos abaixo, foi confirmada como funcionando pelo responsável pelo servidor. Os bancos e domínios de CV/BC refletem a arquitetura documentada; confira a configuração efetiva antes de executar uma nova migração.

## 1. Repositório e pastas

**Novo fluxo disponível:** a criação automática de banco, usuário Admin,
parâmetros, APIs, domínio e HTTPS está documentada em
[Provisionamento automático de tenants](provisionamento-automatico-tenant.md).
Esse fluxo exige instalar o serviço `tenant-provisioner` uma vez no Ubuntu.
Os procedimentos manuais abaixo continuam disponíveis para bancos existentes.

Repositório: https://github.com/cleitonvargasdev/ContratosN — branch `main`.

Commit da implantação inicial do painel Tenant: `77dd9f7`.

| Projeto | Desenvolvimento Windows | Ubuntu |
| --- | --- | --- |
| API compartilhada | `D:\PROJETOINI\API` | `/var/www/apicontratos/ContratosN/API` |
| Frontend das empresas | `D:\PROJETOINI\FRONTEND` | `/var/www/apicontratos/ContratosN/FRONTEND` |
| Painel administrativo Tenant | `D:\PROJETOINI\TENANT` | `/var/www/apicontratos/ContratosN/TENANT` |

Os três projetos estão no mesmo Git. Um único `git pull` atualiza todo o checkout. O Git leva código e scripts; os dados dos bancos, senhas do ambiente e certificados permanecem no servidor.

## 2. Bancos de dados

| Banco | Finalidade |
| --- | --- |
| `tenant_registry` | Administração da plataforma: usuários administrativos, sessões, empresas e domínios |
| `cv_financeiro` | Dados de negócio exclusivos da CV |
| `bc_financeiro` | Dados de negócio exclusivos da BC |
| `Contratos` | Banco original, preservado como origem da separação; também é o banco utilizado no modo legado conforme configuração |

O registro central é um banco independente. Ele não fica dentro de CV/BC e não recebe uma cópia dos contratos. As alterações em uma empresa não são replicadas para a outra.

Tabelas administrativas em `tenant_registry`:

- `cad_usuario`: usuários do painel e hashes de senha.
- `tenant_admin_sessions`: sessões administrativas, com hash do token e validade.
- `tenants`: código da empresa, referências de conexão, URL pública e controles de ativação.
- `tenant_domains`: relação entre domínios e empresas.

Os usuários do painel são independentes dos usuários das empresas. Todo usuário ativo cadastrado nesse painel tem acesso administrativo aos tenants e aos demais usuários do painel.

### Configuração da API

Arquivo de produção: `/var/www/apicontratos/ContratosN/API/.env`.

| Variável | Utilização |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` | Conexão PostgreSQL, inclusive para o registro central |
| `DB_NAME` | Banco de origem/legado; manter `Contratos` na configuração documentada |
| `TENANT_REGISTRY_DB_NAME` | Nome do banco administrativo; padrão `tenant_registry` |
| `TENANCY_ENABLED` | `true` ativa o roteamento por empresa; o painel também funciona com `false` |
| `TENANT_CV_DATABASE_URL` | Conexão exclusiva com o banco da CV |
| `TENANT_BC_DATABASE_URL` | Conexão exclusiva com o banco da BC |
| `TENANT_CV_WEBHOOK_SECRET` | Segredo de webhook da CV, com pelo menos 32 caracteres |
| `TENANT_BC_WEBHOOK_SECRET` | Segredo diferente para o webhook da BC, com pelo menos 32 caracteres |

Não substituir as chaves `JWT_SECRET_KEY` e `SECRET_ENCRYPTION_KEY` durante atualizações de rotina. Dados existentes podem depender delas. Não versionar o `.env` nem colocar senhas de banco em variáveis públicas `VITE_*` do frontend.

Na configuração com PostgreSQL instalado no Ubuntu, a API em Docker pode usar `host.docker.internal`. Na configuração com PostgreSQL no Compose, o host interno é `db`. O endereço `localhost` dentro de um container aponta para o próprio container.

### Inicializar o registro administrativo

O PostgreSQL deve estar disponível. A conta configurada precisa ter permissão para criar o banco, ou o banco deve existir previamente.

```bash
cd /var/www/apicontratos/ContratosN/API

docker compose -f docker-compose.yml -f docker-compose.tenant.yml run --rm --no-deps --entrypoint python api -m scripts.init_tenant_admin
```

O comando cria o registro e suas tabelas. Se `cad_usuario` estiver vazia, cria o acesso inicial **ADMIN / Admin**. Reexecutar preserva usuários e senhas existentes; não é um procedimento de recuperação de senha. Alterar a senha inicial pelo perfil após entrar.

### Vincular empresas com banco existente (modo manual)

1. Preparar o banco exclusivo da empresa e suas migrações.
2. Configurar na API a variável de conexão e o segredo de webhook.
3. Recriar o container da API para carregar alterações no `.env`.
4. Entrar em `https://tenants.vstec.net` e cadastrar código, domínios, URL pública e nomes das variáveis.
5. Habilitar os serviços da empresa quando as integrações estiverem prontas.

O painel não cria bancos PostgreSQL nem registros DNS. Código e referência de banco ficam fixos após o cadastro para evitar troca de banco com conexões abertas.

Para consultar o registro por comando:

```bash
docker compose -f docker-compose.yml -f docker-compose.tenant.yml run --rm --no-deps --entrypoint python api -m scripts.manage_tenants list
```

**Cópia inicial de CV/BC:** seguir [Implantação dos tenants CV e BC](implantacao-tenants-ubuntu.md). O script `scripts/clone_tenant_databases.sh` recusa executar se qualquer destino já existir, inclusive `tenant_registry`. Como o painel já foi instalado, não executar esse script como atualização de rotina nem apagar o registro para permitir a execução. Uma migração ainda pendente deve preservar o registro administrativo existente.

## 3. Domínios e portas

| Domínio | Aplicação | Destino do proxy no Ubuntu | Banco |
| --- | --- | --- | --- |
| `tenants.vstec.net` | Administração Tenant | `127.0.0.1:8081` | `tenant_registry` |
| `cvfinanceiro.vstec.net` | Frontend da CV | `127.0.0.1:8080` | `cv_financeiro`, com multitenant ativo |
| `bcfinanceiro.vstec.net` | Frontend da BC | `127.0.0.1:8080` | `bc_financeiro`, com multitenant ativo |

A API compartilhada atende em `api:8007` na rede Docker. O serviço `web` atende o frontend das empresas; `tenant-web` atende o painel administrativo.

Fluxo do painel:

```text
https://tenants.vstec.net
  → Nginx do Ubuntu / certificado HTTPS
  → 127.0.0.1:8081 / container tenant-web
  → /api/platform/ encaminhado para api:8007
  → tenant_registry
```

`tenants.vstec.net` não deve ser cadastrado como domínio de CV ou BC e não precisa entrar em `TENANT_API_HOSTS`. As rotas administrativas têm autenticação própria.

Para CV/BC, o `APP_DOMAIN` do serviço web deve incluir os domínios das empresas e o frontend deve usar `VITE_API_URL=/api/v1`, conforme o roteiro multitenant.

## 4. Atualização e primeira instalação do painel

Executar os comandos abaixo individualmente. Se algum falhar, corrigir antes de continuar. Eles pressupõem a instalação com PostgreSQL acessível pela configuração atual da API.

```bash
cd /var/www/apicontratos/ContratosN/API

git pull --ff-only origin main

docker compose -f docker-compose.yml -f docker-compose.tenant.yml build api tenant-web

docker compose -f docker-compose.yml -f docker-compose.tenant.yml run --rm --no-deps --entrypoint python api -m scripts.init_tenant_admin

docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d api tenant-web
```

O entrypoint da API executa as migrações de negócio antes de iniciar o serviço. Em modo multitenant, os tenants ativos precisam estar cadastrados e seus bancos acessíveis.

Se a instalação utiliza PostgreSQL pelo arquivo `docker-compose.with-db.yml`, incluir esse arquivo em **todos** os comandos Compose, mantendo o mesmo projeto e os mesmos volumes:

```bash
docker compose -f docker-compose.yml -f docker-compose.with-db.yml -f docker-compose.tenant.yml ps
```

### Atualizações futuras

Após `git pull --ff-only origin main`, executar conforme a alteração:

```bash
# Apenas painel Tenant
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d --build tenant-web

# Apenas API
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d --build api

# Apenas frontend das empresas
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d --build web

# Todos os serviços da aplicação
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d --build api web tenant-web
```

Ao mudar variáveis do `.env`, usar `up -d --force-recreate api` com os mesmos arquivos Compose para carregar o novo ambiente; um simples `restart` não atualiza variáveis do container.

## 5. DNS e Nginx do Ubuntu

O domínio deve resolver para o IP público correto do servidor. Conferir também um eventual registro IPv6. Para emissão HTTP pelo Nginx, o domínio deve estar acessível externamente na porta 80; o site HTTPS utiliza a porta 443.

Conferências:

```bash
getent ahosts tenants.vstec.net
sudo nginx -t
sudo systemctl status nginx --no-pager
```

### Primeira configuração de tenants.vstec.net

Procedimento usado com Nginx instalado diretamente no Ubuntu:

```bash
cd /var/www/apicontratos/ContratosN/API

sudo cp docker/tenant-ubuntu.nginx.example /etc/nginx/sites-available/tenants.vstec.net

sudo ln -sfn /etc/nginx/sites-available/tenants.vstec.net /etc/nginx/sites-enabled/tenants.vstec.net

sudo nginx -t && sudo systemctl reload nginx
```

O arquivo de exemplo encaminha o domínio para `127.0.0.1:8081`. Esta cópia é para a primeira instalação: **não sobrescrever o virtual host já configurado pelo Certbot durante atualizações**, pois isso removeria suas configurações HTTPS.

Arquivos de referência no Git:

- `API/docker/tenant-ubuntu.nginx.example`: virtual host HTTP no Ubuntu.
- `API/docker/tenant-nginx.conf`: Nginx interno do container.
- `API/docker/tenant-nginx.Dockerfile`: build do painel.
- `API/docker-compose.tenant.yml`: serviço `tenant-web` e porta local 8081.

Se outro proxy gerencia o servidor, configurar domínio, destino e certificado nesse proxy. Não duplicar o mesmo domínio em dois gerenciadores. Em proxy dentro de container, `127.0.0.1` representa esse container; o destino deve ser adaptado à rede real.

## 6. Instalação e emissão dos certificados

Procedimento utilizado nesta implantação, com pacotes Ubuntu e plugin Nginx:

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

sudo certbot --nginx -d tenants.vstec.net --redirect
```

Preencher as solicitações interativas do Certbot, incluindo contato e aceite dos termos. O plugin configura HTTPS no Nginx e o redirecionamento HTTP → HTTPS. [Referência oficial do Certbot](https://eff-certbot.readthedocs.io/en/stable/using.html).

Para uma **primeira emissão** nos domínios das empresas, depois de configurar DNS e seus virtual hosts:

```bash
sudo certbot --nginx -d cvfinanceiro.vstec.net --redirect
sudo certbot --nginx -d bcfinanceiro.vstec.net --redirect
```

Esses comandos são referência para instalação; não é necessário reemitir certificados a cada deploy. Conferir certificados existentes antes de emitir novamente:

```bash
sudo certbot certificates
```

O comando mostra nomes, domínios, validade e caminhos reais. Os arquivos normalmente ficam sob `/etc/letsencrypt/live/<nome-do-certificado>/`; o nome pode ter sufixo. Manter chaves privadas no servidor, fora do Git.

## 7. Renovação dos certificados

Testar a renovação sem substituir o certificado de produção:

```bash
sudo certbot renew --dry-run
```

Conferir se há agendamento ativo no servidor:

```bash
systemctl list-timers --all | grep -i certbot
```

A instalação pode usar timer ou cron; a ausência nessa listagem, sozinha, não confirma ausência de renovação automática. Conferir o mecanismo instalado antes de criar outro agendamento. [Renovação automática na documentação oficial](https://eff-certbot.readthedocs.io/en/stable/using.html#automated-renewals).

Para solicitar a renovação dos certificados elegíveis e recarregar o Nginx após sucesso:

```bash
sudo certbot renew
sudo nginx -t && sudo systemctl reload nginx
```

Não usar renovação forçada como rotina. Acompanhar validade com `sudo certbot certificates` e resolver falhas no teste de renovação.

## 8. Conferência após implantação

```bash
cd /var/www/apicontratos/ContratosN/API

docker compose -f docker-compose.yml -f docker-compose.tenant.yml ps

docker compose -f docker-compose.yml -f docker-compose.tenant.yml logs --tail=100 api tenant-web

curl -I http://127.0.0.1:8081/
curl -i http://127.0.0.1:8081/api/platform/tenants
curl -I https://tenants.vstec.net
```

Resultado esperado: frontend responde **200**, rota administrativa sem login responde **401** e acesso público utiliza HTTPS válido. Entrar no navegador e conferir os cadastros de usuários e tenants.

## 9. Diagnóstico rápido

| Sintoma | O que conferir |
| --- | --- |
| Erro 502 no domínio | Containers, logs, porta 8081 e destino do proxy |
| 502 após recriar a API | Nginx interno pode manter o IP anterior; reiniciar `web` e `tenant-web` com os mesmos arquivos Compose |
| Login ADMIN não funciona | Banco de registro correto, execução do inicializador, usuário ativo e senha atual; o inicializador não redefine senha |
| Mensagem de muitas tentativas | Aguardar cinco minutos após bloqueio de login |
| API não inicia em modo multitenant | Registro, tenants ativos, conexões e migrações dos bancos |
| Cadastro de tenant rejeitado | Variáveis configuradas na API, banco exclusivo, domínio único e webhook com segredo de pelo menos 32 caracteres |
| Certbot não valida domínio | DNS IPv4/IPv6, porta 80 acessível e virtual host correto |
| Certificado próximo do vencimento | `certbot certificates`, `renew --dry-run` e agendamento de renovação |
| Git pull interrompido por alterações locais | Conferir `git status` e preservar alterações; não executar reset destrutivo como atualização padrão |

## 10. Preservação e referências

Preservar backups separados de `tenant_registry`, dos bancos das empresas e do banco original enquanto ele for necessário. Preservar também o `.env`, as chaves de criptografia e a configuração do proxy em local de acesso restrito. Um commit Git não é backup do PostgreSQL.

Não executar `docker compose down -v` como rotina de atualização: a opção remove volumes gerenciados pelo Compose e pode eliminar os dados do PostgreSQL em container.

Documentos complementares:

- [Implantação do painel Tenant](implantacao-painel-tenant.md).
- [Implantação dos tenants CV e BC](implantacao-tenants-ubuntu.md).
- [README do projeto Tenant](../../TENANT/README.md).

Este documento registra os procedimentos. Sua criação não executa comandos nem altera a instalação do Ubuntu.
