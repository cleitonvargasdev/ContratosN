# Criação automática de empresas no Ubuntu

O painel Tenant passa a oferecer **Criar tenant e publicar site**, além da opção **Vincular banco existente**. O cadastro automático exige um domínio já apontado diretamente para o Ubuntu. A instalação do serviço abaixo é feita uma vez; depois o cadastro e o acompanhamento são realizados no painel.

## O que é criado

- Um banco PostgreSQL novo e um usuário PostgreSQL exclusivo, com senha aleatória; banco e role usam identificador interno `tenant_<id-do-processo>`.
- Todas as tabelas na versão atual do Alembic. Permanecem os cadastros básicos de localidades fornecidos pelas migrações.
- Perfis e permissões da configuração inicial. O perfil **Administrador** fica ativo e recebe acesso completo ao catálogo atual.
- Apenas um usuário: nome/função **Administrador**, login **Admin**, senha **Admin**, perfil **Administrador**. Email inicial `admin@<domínio>`; alterar depois se necessário.
- Parâmetros com nome fantasia **Sua empresa** e razão social **Sua razão social**, editáveis no cadastro.
- Regras de score, regras do nono dígito e configuração básica de cobrança salvas no Tenant. Agendamentos e automações começam desativados.
- Cadastros de APIs da configuração inicial, vinculados ao novo administrador; nenhum usuário de origem é copiado.
- Integração **quepasa**. O formulário sugere usuário, sufixo, país e mensagens da configuração inicial. Permite usar o token salvo sem exibi-lo ou informar outro token.
- Virtual host Nginx, certificado HTTPS e teste de login no domínio novo.

Não são copiados clientes, contratos, recebimentos, contas, produtos, fornecedores, histórico, sessões ou chaves de acesso de usuários das empresas existentes. A seleção de configurações é explícita, sem clonar o banco de negócio.

WhatsApp começa desativado no registro: reaproveitar um token pode apontar para a mesma conexão da empresa modelo. Conferir a conexão exclusiva antes de ativar WhatsApp e automações no painel. A criação do site não conecta dispositivos nem altera webhooks do Quepasa.

## De onde vêm os padrões

Os padrões ficam na tabela `tenant_bootstrap_config` do banco central `tenant_registry`, com conteúdo criptografado, versão, data e login do último administrador que salvou. O provisionamento não consulta mais um banco de empresa para obter os padrões.

A carga de instalação está em `app/tenancy/initial_config.json`, exportada dos dados atuais: 2 perfis, 5 APIs e os parâmetros permitidos, sem usuários, clientes ou movimentações. O arquivo é criptografado porque contém também credenciais de integrações. **Preservar no ambiente de destino a chave que gerou o arquivo (`SECRET_ENCRYPTION_KEY`, ou `JWT_SECRET_KEY` quando usada como alternativa).** Uma chave diferente impede a primeira carga; não há inserção parcial da configuração.

Ao iniciar o container com multitenancy ou provisionamento habilitado, o entrypoint cria o registro se necessário e executa `scripts.init_tenant_admin`. A primeira carga insere a configuração; as seguintes preservam edições e senhas existentes. A API também verifica a tabela de configuração ao iniciar. Fora do Docker, criar o registro inicialmente com `python -m scripts.init_tenant_admin`.

### Editar pelo painel

Abrir **Configuração inicial** no menu Tenant. O formulário permite editar nomes sugeridos da empresa, score, cobrança, WhatsApp, regras do nono dígito, perfis/permissões e cadastros de APIs. O perfil Administrador sempre recebe acesso completo na criação.

O token WhatsApp não é retornado ao navegador: escolher manter, substituir ou remover. Os cadastros de APIs são acessíveis somente a administradores autenticados; as respostas desse formulário usam `Cache-Control: no-store`.

Salvar afeta apenas novas criações. Cada processo guarda uma cópia dos dados e da versão utilizada, preservada nas retomadas. Uma edição baseada em versão antiga é recusada: recarregar antes de salvar novamente. WhatsApp, agendamentos e automações continuam desativados inicialmente.

### Gerar outra carga de instalação (opcional)

`python -m scripts.export_tenant_initial_config` exporta explicitamente os dados permitidos do banco indicado por `TENANT_TEMPLATE_CODE`, ou de `DB_NAME` quando a variável está vazia. Substitui o arquivo de instalação, sem alterar uma configuração já salva no registro. Esse comando só é necessário para preparar outra carga; o funcionamento normal não depende da empresa modelo. Não incluir a chave de criptografia no código-fonte.

## Arquitetura operacional

```text
Painel Tenant → API → fila no tenant_registry
                      ↓
Serviço systemd no Ubuntu (um worker por instalação)
  → valida DNS
  → comando interno no container: cria banco, migra e inicializa
  → Nginx do Ubuntu → Certbot
  → testa HTTPS, frontend e login Admin na empresa correta
  → marca como pronto
```

A API não recebe acesso ao socket Docker nem executa comandos do Nginx. O serviço do Ubuntu executa comandos fixos e valida os domínios. As operações administrativas dependem do acesso ao painel.

Credenciais geradas ficam em `API/tenant-runtime/secrets`, fora do Git e da imagem Docker, com acesso restrito. A API lê esse volume ao resolver cada tenant; criar uma empresa não exige recriar a API. Fazer backup desse diretório junto com `tenant_registry`, bancos de negócio e chaves de criptografia do `.env`.

## Preparar o Ubuntu uma vez

Este procedimento corresponde à instalação com Nginx diretamente no Ubuntu e PostgreSQL já configurado na API. Se usa outro proxy ou DNS com proxy/CDN, adaptar antes: o worker exige que todos os endereços DNS do novo domínio estejam na lista de IPs configurada e gerencia virtual hosts em `/etc/nginx/sites-available`.

### 1. Atualizar o código e preparar o ambiente

```bash
cd /var/www/apicontratos/ContratosN/API
git pull --ff-only origin main
sudo apt-get update
sudo apt-get install -y python3 certbot python3-certbot-nginx
sudo install -d -m 700 tenant-runtime
nano .env
```

Adicionar/confirmar no `.env`:

```dotenv
TENANCY_ENABLED=true
TENANT_PROVISIONING_ENABLED=true
TENANT_REGISTRY_DB_NAME=tenant_registry
TENANT_TEMPLATE_CODE=
```

Antes de ativar `TENANCY_ENABLED`, conferir o cadastro e as conexões das empresas existentes; essa opção muda o roteamento de negócio. Se a instalação for nova e ainda não houver empresas, a API permite iniciar o painel com provisionamento habilitado.

A conta administrativa PostgreSQL configurada em `DB_USER` precisa conseguir criar roles, bancos e atribuir o novo proprietário. Uma conta PostgreSQL administrativa atende ao fluxo; uma conta sem esses privilégios gera falha na etapa Banco. As conexões de cada nova empresa usam sua própria role, sem poderes de criação de bancos, roles ou superusuário.

Preservar `JWT_SECRET_KEY` e `SECRET_ENCRYPTION_KEY`: protegem os tokens e as configurações da fila.

### 2. Construir, inicializar registro e subir

```bash
docker compose -f docker-compose.yml -f docker-compose.tenant.yml build api web tenant-web
docker compose -f docker-compose.yml -f docker-compose.tenant.yml run --rm --no-deps --entrypoint python api -m scripts.init_tenant_admin
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d api web tenant-web
```

O inicializador adiciona `tenant_provision_jobs` e `tenant_bootstrap_config` ao registro e preserva seus usuários e configurações existentes. As migrações de negócio ampliam o campo do token WhatsApp para comportar criptografia. Usar os dois arquivos Compose em todas as atualizações para preservar o volume de credenciais.

Se usa `docker-compose.with-db.yml`, incluí-lo em todos os comandos e na configuração do worker abaixo, mantendo o mesmo projeto Compose e seus volumes.

### 3. Configurar IPs públicos e contato dos certificados

```bash
sudo install -m 600 docker/tenant-provisioner.env.example /etc/tenant-provisioner.env
sudo nano /etc/tenant-provisioner.env
```

Preencher com os valores reais, sem aspas quando não houver espaços:

```dotenv
TENANT_API_DIR=/var/www/apicontratos/ContratosN/API
TENANT_COMPOSE_FILES=docker-compose.yml,docker-compose.tenant.yml
TENANT_PUBLIC_IPS=IP_PUBLICO_REAL_DO_SERVIDOR
TENANT_CERTBOT_EMAIL=EMAIL_REAL_DO_RESPONSAVEL
```

Se houver IPv4 e IPv6 válidos, separar por vírgula. Um registro AAAA que aponte para outro servidor bloqueia a criação. O endereço do domínio não pode incluir protocolo, porta ou caminho.

Para PostgreSQL no Compose, a lista é `docker-compose.yml,docker-compose.with-db.yml,docker-compose.tenant.yml`.

### 4. Instalar e iniciar o serviço

```bash
sudo install -m 644 docker/tenant-provisioner.service /etc/systemd/system/tenant-provisioner.service
sudo systemctl daemon-reload
sudo systemctl enable --now tenant-provisioner
sudo systemctl status tenant-provisioner --no-pager
sudo journalctl -u tenant-provisioner -n 100 --no-pager
```

Se o checkout fica em outro caminho, ajustar também `ExecStart` no arquivo do serviço. O serviço usa root para Nginx, Certbot e comandos Docker; manter o checkout e `/etc/tenant-provisioner.env` acessíveis somente a administradores autorizados.

Os logs mostram código da empresa e etapa, sem tokens ou senhas. O worker atualiza seu sinal de atividade a cada 15 segundos. O painel só aceita novas criações quando esse sinal está recente e as opções de provisionamento/multitenant estão ativas.

## Cadastrar pelo painel

1. Apontar o domínio para os IPs do Ubuntu e aguardar a propagação DNS.
2. Entrar em `https://tenants.vstec.net` e clicar em **Novo tenant**.
3. Informar código e domínio, revisar nome fantasia, razão social e WhatsApp.
4. Conferir os perfis, quantidade de APIs e regras de score apresentados.
5. Clicar em **Criar e publicar**.
6. Acompanhar domínio, banco, site, certificado e verificação na lista.
7. Quando aparecer **Pronto para usar**, clicar em **Abrir site** e entrar como `Admin` / `Admin`.

Trocar a senha inicial e completar os dados da empresa. Uma criação bem-sucedida fica ativa para login; automações e WhatsApp continuam desativados até configuração explícita.

## Falhas e retomada

O código e o domínio são reservados na fila. Se uma etapa falhar, o tenant fica inativo e o painel oferece **Retomar criação** depois de corrigir a causa no Ubuntu.

- DNS: conferir os registros A/AAAA e `TENANT_PUBLIC_IPS`.
- Banco: conferir permissões, conectividade e migrações.
- Nginx: conferir `sudo nginx -t` e virtual hosts já existentes para o mesmo domínio.
- Certificado: conferir porta 80, DNS e `/var/log/letsencrypt/letsencrypt.log`.
- Verificação: conferir acesso HTTPS, frontend na porta 8080 e API, incluindo os logs dos containers.

Reexecutar preserva banco, senha gerada, usuário, parâmetros e configurações já inicializados. Há marcações de propriedade no banco/role e no virtual host. O worker não adota bancos ou arquivos já existentes de outra origem nem os apaga. Se ocorrer uma interrupção exatamente entre criar o banco e gravar sua marcação, a retomada exige revisão administrativa dessa propriedade no PostgreSQL; não excluir automaticamente o banco.

Se reiniciar o worker durante uma tarefa, ele retoma as tarefas em andamento. Instalar apenas um worker por registro central; a trava local impede duas instâncias simultâneas no mesmo Ubuntu.

Na verificação final, o acesso é habilitado para testar o login real. Falha desativa novamente; a indicação **Pronto** só é gravada depois do teste. A credencial inicial é utilizada apenas nesse teste, sem ser escrita nos logs.

Domínios de tenants provisionados não podem ser alterados diretamente no cadastro: uma troca exige manutenção do virtual host e do certificado. Os controles de ativação e serviços continuam editáveis.

## Atualizações do provisionador

```bash
cd /var/www/apicontratos/ContratosN/API
sudo systemctl stop tenant-provisioner
git pull --ff-only origin main
docker compose -f docker-compose.yml -f docker-compose.tenant.yml build api web tenant-web
docker compose -f docker-compose.yml -f docker-compose.tenant.yml run --rm --no-deps --entrypoint python api -m scripts.init_tenant_admin
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d api web tenant-web
sudo systemctl start tenant-provisioner
```

Não recopie o arquivo de ambiente de exemplo sobre a configuração real a cada atualização. Se o arquivo `.service` mudar, reinstalar esse arquivo e executar `daemon-reload` antes de iniciar o serviço.

Os certificados criados usam nomes `tenant-<id-do-processo>`. A renovação segue o Certbot existente: `sudo certbot certificates` e `sudo certbot renew --dry-run`. Consultar [Processos Ubuntu](Processos%20Ubuntu.md).

## Limites da validação em desenvolvimento

A lógica de criação, o PostgreSQL real temporário e o build do painel são verificáveis localmente. A emissão real de certificados e a configuração do Nginx devem ser confirmadas no Ubuntu após instalar o serviço; não foram executadas no servidor por este desenvolvimento.
