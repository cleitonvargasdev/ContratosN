# Carteira SQLite — versão 1.1.0 do aplicativo

## Funcionalidade implementada

A carteira é selecionada pelo usuário responsável pelo cliente (`clientes.usuario_id`), comparado ao ID do usuário autenticado. O vendedor do contrato (`contratos.usuario_id_vendedor`) não define a carteira do app. Exporta todas as parcelas com `quitado` diferente de verdadeiro e saldo positivo (`valor_total - valor_recebido`), inclusive parciais e a vencer. Não aplica filtro de atraso ou UF nesta etapa de carga completa.

Um único SELECT com JOINs lê parcelas, contratos, clientes e localidades no banco do tenant atual. O SQLite é preenchido em uma transação, fechado e compactado no servidor. As tabelas são `metadata`, `usuario`, `clientes`, `contratos` e `parcelas`. Contratos incluem observação, indicador de comodato e ID da negociação. O cadastro local de usuário contém somente ID, nome e login; não leva senha, hash, chave de API nem permissões administrativas.

Valores monetários são inteiros na escala 10.000 para preservar quatro casas decimais da API. O limite inicial é de 200.000 parcelas por exportação; acima disso a carga falha explicitamente, sem truncar a carteira.

## Rotas autenticadas

- `POST /api/v1/mobile/carteira`: gera a carga e devolve ID, SHA-256, tamanhos do ZIP/SQLite, contagens e versão do esquema.
- `GET /api/v1/mobile/carteira/{id}/arquivo`: entrega o ZIP somente ao usuário/tenant que o gerou.
- `POST /api/v1/mobile/carteira/{id}/confirmar`: exclui o ZIP desse usuário/tenant. Repetir a confirmação retorna 204 mesmo se o arquivo já não existir.

Todas as rotas revalidam o usuário ativo e a permissão `acesso_web`, mantendo a regra atual do login. Não recebem ID de outro cobrador nem nome do banco. Um ID de carga de outro usuário não permite baixar ou apagar seu arquivo.

Os artefatos ficam em `MOBILE_WALLET_DIR` quando configurado; por padrão, na pasta temporária `contratos-mobile-wallets` dentro do container. Expiram após 24 horas; a limpeza roda a cada hora e na geração de uma nova carga. O `docker-compose.yml` usa o volume gerenciado `mobile_wallets` em `/var/lib/contratos/mobile-wallets`, portanto uma recriação normal do container preserva cargas ainda não baixadas. Com várias réplicas, será necessário armazenamento compartilhado entre todas elas.

## Instalação e consulta no aparelho

Em **Visitas** ou **Transmissão**, tocar em **Baixar carteira completa**. O aplicativo valida tamanho, SHA-256, conteúdo único do ZIP, integridade SQLite, esquema, empresa, usuário, ID de carga e contagens antes de ativar a carteira. Não usa caminhos fornecidos pelo ZIP para extrair arquivos. Limites: ZIP de 64 MiB e SQLite de 256 MiB.

Cada empresa/usuário tem uma pasta local própria. O ponteiro para a carteira ativa e a confirmação pendente são gravados juntos em uma transação no banco de movimentações. Somente após instalar e persistir, o aplicativo confirma o recebimento para excluir o ZIP no servidor. Falha na confirmação mantém a carteira disponível e uma pendência local; usar **Repetir confirmação de recebimento** ou concluir uma nova carga para repetir a limpeza.

Clientes, contratos, observações e parcelas podem ser consultados sem internet. A sessão é armazenada com `flutter_secure_storage`, sem senha, permitindo reabrir o aplicativo offline após um login bem-sucedido. Cada operação online passa pela API; o app tenta renovar o token uma vez quando recebe 401. Bloqueio remoto só é conhecido quando houver comunicação. Sair remove a sessão, mas preserva a carteira local segregada pelo usuário e empresa.

O app registra recebimentos, GPS de visitas e ocorrências localmente no banco de operações, separado da carteira. O envio e o processamento de lotes ainda não foram integrados à API; os registros permanecem pendentes no aparelho e o download de uma nova carteira fica bloqueado enquanto existirem pendências. Portanto, esta versão ainda não substitui o aplicativo operacional.

## Implantar a API no Ubuntu

Atualizar estes arquivos na pasta `/var/www/apicontratos/ContratosN/API`, preservando os arquivos de ambiente:

```text
app/services/mobile_wallet_service.py
app/controllers/mobile_wallet_controller.py
app/api/v1/router.py
app/main.py
docker-compose.yml
```

Não há migração de banco para esta funcionalidade. Depois de enviar os arquivos:

```bash
cd /var/www/apicontratos/ContratosN/API
docker compose -f docker-compose.yml -f docker-compose.tenant.yml up -d --build --no-deps api
docker compose -f docker-compose.yml -f docker-compose.tenant.yml logs --tail 60 api
```

O volume `mobile_wallets` é criado automaticamente no primeiro `up`. Não usar
`docker compose down -v` durante atualizações: esse comando remove os volumes
gerenciados, inclusive as carteiras que ainda aguardam download.

Após aparecer `Application startup complete`, recarregar os proxies, como foi necessário na configuração do domínio:

```bash
docker compose -f docker-compose.yml -f docker-compose.tenant.yml exec -T web nginx -s reload
docker compose -f docker-compose.yml -f docker-compose.tenant.yml exec -T tenant-web nginx -s reload
curl --fail https://api.vstec.net/health
```

O novo APK precisa dessas rotas implantadas; um 404 no download pode indicar API antiga. Instalar o APK 1.2.0+3 sobre o anterior, assinado com a mesma chave, fazer login como cobrador com clientes vinculados, baixar e conferir a carteira. Testar também modo avião, fechar/reabrir o app e consultar os contratos. Um usuário sem clientes atribuídos recebe uma carteira vazia, mesmo se for administrador.

## Validação local

- Testes Python: filtro efetivo do SELECT, saldo parcial, observações, geração ZIP/SQLite, integridade, precisão, expiração, segregação por empresa/usuário, confirmação repetida e autorização das rotas.
- Testes Flutter: instalação de um ZIP produzido pelo serviço Python em SQLite real, consulta do saldo, rejeição de SHA incorreto e de carteira de outro usuário, rejeição de caminho de extração indevido, persistência/repetição de confirmação pendente, além dos testes anteriores de autenticação e UI.
- Produção: login da versão anterior confirmado pelo usuário. A nova carteira ainda precisa ser validada com dados reais após implantar a API; nenhum recebimento foi alterado nestes testes.
