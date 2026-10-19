# Domínio de produção do aplicativo

Endereço do aplicativo: `https://api.vstec.net/api/v1`. Em 19/10/2026, o DNS local resolveu `api.vstec.net` para `46.62.156.67`. O HTTPS não pôde ser validado deste ambiente: houve erro de confiança no certificado e falha de conexão na consulta de diagnóstico. Isso não confirma a configuração efetiva do servidor.

Atualização após configuração pelo usuário: HTTPS e `/health` validados com HTTP 200. `TENANCY_ENABLED=true` e `TENANT_API_HOSTS=api.vstec.net` confirmados no container. O Certbot instalou o bloco de `api.vstec.net` em `00-default.conf`; foi necessário substituir o `return 444` somente desse bloco pelo proxy para `127.0.0.1:8080`. Os servidores padrão mantiveram `return 444`.

Após recriar a API, o frontend apresentou 502 até recarregar os proxies com os comandos abaixo. A instalação real usa `/var/www/apicontratos/ContratosN/API`:

```bash
docker compose -f docker-compose.yml -f docker-compose.tenant.yml exec -T web nginx -s reload
docker compose -f docker-compose.yml -f docker-compose.tenant.yml exec -T tenant-web nginx -s reload
```

## Configuração no Ubuntu

Não cadastrar `api.vstec.net` como domínio de CV, BC ou outra empresa no painel tenant. Ele deve ser um host neutro. No `.env` da API, manter o multitenant ativo e incluir o host (preservar outros hosts neutros já existentes, separados por vírgula):

```dotenv
TENANCY_ENABLED=true
TENANT_API_HOSTS=api.vstec.net
```

Adicionar também `api.vstec.net` à lista existente de `APP_DOMAIN`, preservando os domínios das empresas. A arquitetura documentada usa o Nginx do Ubuntu encaminhando ao serviço `web` na porta 8080, que encaminha `/api/` à API. O proxy precisa preservar o cabeçalho Host nos dois trechos.

Na pasta da API, recriar os serviços para carregar o `.env`, usando os mesmos arquivos Compose utilizados na implantação. Exemplo para a implantação com painel tenant:

```bash
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d --force-recreate api web
```

O arquivo `docker/mobile-api-ubuntu.nginx.example` contém o virtual host inicial HTTP. Se já houver virtual host desse nome, integrar nele em vez de criar duplicado. Para uma instalação nova, no layout padrão do Nginx Ubuntu:

```bash
sudo install -m 644 docker/mobile-api-ubuntu.nginx.example /etc/nginx/sites-available/api.vstec.net
sudo ln -s /etc/nginx/sites-available/api.vstec.net /etc/nginx/sites-enabled/api.vstec.net
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d api.vstec.net --redirect
curl --fail https://api.vstec.net/health
```

Executar reload somente se `nginx -t` passar. Usar o Certbot já previsto na implantação e liberar as portas 80/443 no servidor. Não desabilitar validação TLS no aplicativo.

## Seleção do tenant

Enviar `POST /api/v1/auth/login` como formulário `application/x-www-form-urlencoded`, com `company_code`, `username` e `password`. Nas próximas requisições enviar o Bearer token; a API identifica o banco pelo `tenant_id` assinado. Não embutir credenciais nem chave administrativa no APK.

A rota `/health` verifica disponibilidade, não valida isolamento entre tenants. Após configurar o domínio, testar login com contas autorizadas de cada empresa, `/auth/me` e rejeição de token de outra empresa nos domínios específicos.

## Compilação local

O aplicativo contém `config/production.json` e `lib/config/api_config.dart` com esse endereço. A integração HTTP ainda precisa ser implementada. Após instalar Android SDK/JDK e configurar a chave de assinatura release:

```powershell
Set-Location D:\PROJETOINI\APP
D:\PROJETOINI\flutter-sdk\bin\flutter.bat build apk --release --dart-define-from-file=config/production.json
```

Saída esperada: `build/app/outputs/flutter-apk/app-release.apk`. A assinatura release deve ser configurada explicitamente: o template inicial do Flutter pode usar a chave de debug no build release. Ainda não foi gerado APK de produção.

Atualização em 19/10/2026: APK release 1.0.0+1 gerado no caminho acima, com chave própria configurada no Gradle e assinatura validada. O login HTTP está implementado; download da carteira e envio de lotes continuam pendentes. Android SDK instalado e JDK 21 configurado. Para repetir o build neste Windows, o script `APP/scripts/build-production.ps1` configura temporariamente o Java para usar os certificados confiáveis do Windows, necessários para o acesso aos repositórios de dependências neste ambiente. Nenhuma validação TLS é desativada no aplicativo.
