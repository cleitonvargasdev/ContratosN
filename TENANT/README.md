# Tenant

Frontend administrativo independente em Vue 3 e Vite. Usa a mesma API do projeto `../API`, nas rotas `/api/platform`. Usuários administrativos ficam na tabela `cad_usuario` do banco `tenant_registry`, separados dos usuários das empresas.

## Iniciar

Na pasta da API, com PostgreSQL acessível e o `.env` configurado:

```powershell
cd D:\PROJETOINI\API
.\.venv\Scripts\python.exe -m scripts.init_tenant_admin
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

O inicializador cria o banco de registro se necessário e suas tabelas. Cria `ADMIN` / `Admin` apenas quando `cad_usuario` estiver vazia. Não redefine senhas e não altera bancos de negócio.

```powershell
cd D:\PROJETOINI\TENANT
npm.cmd install
npm.cmd run dev
```

Acesse **http://127.0.0.1:5175**. Login inicial: **ADMIN**, senha: **Admin**. Clique no seu usuário, no cabeçalho, para trocar a senha. A troca encerra suas sessões. Cada usuário ativo deste painel tem poderes administrativos sobre todos os tenants e usuários.

Copie `.env.example` para `.env.local` se precisar alterar a porta da API. Não coloque senhas de banco ou segredos em variáveis `VITE_*`: elas são públicas no navegador.

## Criação automática de empresas

O botão Novo tenant abre o formulário para criar uma empresa com banco vazio,
usuário Admin / Admin, perfil Administrador, parâmetros genéricos, regras de
score e cadastros de APIs copiados do modelo. Os dados do WhatsApp são sugeridos
e podem ser ajustados. A fila mostra cada etapa, falhas e a opção de retomar.

Esse fluxo depende da instalação única do serviço no Ubuntu conforme
[Provisionamento automático](../API/docs/provisionamento-automatico-tenant.md).
O domínio deve estar previamente apontado. Somente o worker configura o Nginx
e emite o certificado. O frontend não precisa receber credenciais PostgreSQL.

## Vincular banco existente (modo manual)

Prepare o banco PostgreSQL exclusivo da empresa, execute as migrações de negócio e configure na API as variáveis `TENANT_<CODIGO>_DATABASE_URL` e `TENANT_<CODIGO>_WEBHOOK_SECRET` (segredo com pelo menos 32 caracteres). Reinicie a API após alterar variáveis do processo. Depois cadastre no painel:

- Código da empresa, domínios e URL pública.
- Nomes das variáveis de conexão e webhook (nunca os valores secretos).
- Ativação do tenant, automações e WhatsApp.

O modo manual vincula o banco já preparado ao registro central. A criação automática do banco e do site fica no fluxo descrito acima. O DNS deve ser configurado previamente nos dois casos. Código e referência de banco ficam fixos depois do cadastro para evitar troca de banco enquanto há conexões abertas. Tenants podem ser desativados; não há exclusão destrutiva. Domínios adicionais existentes são preservados ao editar.

O roteamento das empresas depende de `TENANCY_ENABLED=true` na API. O painel administrativo funciona independentemente dessa opção. Consulte também `../API/docs/implantacao-tenants-ubuntu.md` para implantação e ativação dos serviços.

## Build e publicação

```powershell
npm.cmd run build
```

Sirva `dist/` por HTTPS, encaminhando `/api/platform/` para a API pelo proxy reverso. O proxy de desenvolvimento Vite não acompanha o build. Se utilizar outra origem de API, configure `VITE_API_BASE_URL` antes do build e autorize a origem do painel no CORS da API. Não há publicação automática.

As sessões duram uma hora, ficam em `sessionStorage` e têm apenas seu hash armazenado no banco. Logout, alteração de senha e desativação revogam o acesso. Cinco tentativas erradas bloqueiam o login por cinco minutos. Tokens de usuários das empresas não dão acesso administrativo.
