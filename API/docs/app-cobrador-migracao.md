# Migração do aplicativo do cobrador

## Etapa atual — 20/10/2026

Ver [app operacional 1.2](app-operacional-1.2.md) para telas, regras implementadas, validação e limites da etapa local. Envio de lotes, integração de solicitações e biometria continuam pendentes.

## Referências visuais

Consultar o [índice de referências do app](referencias-app/README.md) antes de construir as telas. A [página inicial](referencias-app/pagina-inicial.md) registra o menu e a disposição apresentados pelo usuário.

A [tela de transmissão](referencias-app/transmissao.md) registra a seleção de estados, o download da carteira e o envio dos recebimentos do período.

A [tela de clientes e consolidado](referencias-app/clientes.md) registra a ordem de visitas e as visões “Restando” (ainda não visitados), “Todas” (visitados e não visitados) e “Fora da lista” (vencimentos futuros disponíveis para recebimento). O usuário solicita modernizar a apresentação, preservando esse funcionamento.

A [tela de contratos do cliente](referencias-app/contratos-cliente.md) é aberta ao selecionar um cliente e apresenta os contratos separadamente, legendas financeiras e a opção de marcar o cliente como “Fechado”.

A [tela de recebimento por contrato](referencias-app/recebimento-contrato.md) registra seleção de parcelas, distribuição de um valor total, edição direta com excedente como juros e ocorrência “Não pagou”. Documenta também a proposta de GPS obrigatório com exceção após 30 segundos sem obter posição, desde que o serviço esteja ligado.

O [fluxo de solicitações](referencias-app/solicitacoes.md) registra lista, seleção de cliente e formulário. Deve permitir pré-cadastro no app e integrar a solicitação ao módulo web existente, aproveitando seu fluxo de análise e vínculo com cliente/contrato.

Registro de requisitos relatados pelo usuário em 19/10/2026. Documento de planejamento; não representa funcionalidades já implementadas na nova plataforma. Atualizar conforme novas definições forem fornecidas.

## Contexto e carga da carteira

- O aplicativo atual foi desenvolvido em WinDev. A tecnologia será substituída. O usuário está considerando **Flutter com SQLite**; registrar como opção preferida em avaliação, ainda sem decisão definitiva.
- Hoje o acesso informa banco de dados, login e senha. Na nova plataforma, o código da empresa identifica o tenant.
- O cobrador baixa sua carteira inteira, com parcelas em aberto, incluindo saldo de pagamentos parciais e parcelas a vencer. Existem filtros no sistema atual, como estados e dias de atraso; seu comportamento na migração ainda será detalhado.
- A API copia uma base modelo local do aplicativo, seleciona os dados da carteira conforme os filtros, preenche a cópia, compacta e devolve um link de download.
- O aplicativo baixa, descompacta e substitui sua base local. O objetivo é preservar esse fluxo de carga completa, sem popular a carteira registro por registro a partir de JSON no celular.
- A base precisa conter também os dados relacionados necessários às telas de clientes, contratos e parcelas.
- Depois da carga, o cobrador pode trabalhar o dia inteiro offline. O envio das movimentações é feito em lote via JSON, normalmente ao final do dia.

## Visitas, contratos e localização

- Atualmente o cobrador pode reorganizar a ordem da lista de visitas no aplicativo.
- A intenção é passar essa organização para o sistema web principal, com possibilidade de ordenar automaticamente a rota, em uma abordagem semelhante ao problema do caixeiro viajante. Algoritmo, restrições e integração de mapas ainda não foram definidos.
- Incluir a observação do contrato no aplicativo, para informações como comodato, negociação e outros comentários. Ainda não foi definido se o aplicativo poderá editar esse campo ou apenas consultá-lo.
- O aplicativo atual captura coordenadas GPS e as envia junto com o valor recebido. Preservar o funcionamento offline quando houver localização disponível no aparelho.
- Fechado e não pagou são tratados pelo negócio como **ocorrências**.
- As telas de referência também mostram consulta de clientes, contratos, parcelas, solicitações, situação de envio e atualização de localização.

## Lote pai informado pelo usuário

O servidor recebe o JSON e grava um lote pai com as informações gerais abaixo. Os nomes refletem o relato, sem definir ainda o esquema físico da nova plataforma.

| Campo | Observação |
| --- | --- |
| Data | Data geral do lote; origem a definir |
| Hora | Hora geral do lote; origem a definir |
| Numero_Parcelas | Quantidade de parcelas do lote |
| Numero_Ocorrencias | Quantidade de ocorrências do lote |
| Contrato | Citado também no pai; confirmar significado para lotes com vários contratos |
| Parcela | Citado também no pai; confirmar significado para lotes com várias parcelas |
| Valor_Lote | Valor total do lote |
| ID_Usuario | Usuário responsável |
| Processado | Indicador de processamento |
| Bloqueado | Indicador de bloqueio |

O servidor devolve um identificador do lote após gravar o lote e seus itens.

## Itens do lote informados pelo usuário

| Campo | Observação |
| --- | --- |
| Data (cel) | Data registrada no celular |
| Hora (cel) | Hora registrada no celular |
| data_hora_Processamento | Momento do processamento no servidor |
| Contrato | Contrato da movimentação |
| Parcela | Parcela da movimentação |
| Valor | Valor recebido |
| Flag_N_Pagou | Ocorrência de não pagamento |
| Flag_Fechado | Ocorrência de estabelecimento/local fechado |
| Flag_Processado | Indicador de processamento do item |
| Flag_Bloqueado | Indicador de bloqueio do item |
| Motivo_Bloqueio | Motivo do bloqueio |

As coordenadas GPS acompanham os recebimentos. Os nomes dos campos e a captura de coordenadas em cada tipo de ocorrência ainda precisam ser detalhados.

O processamento aplica os pagamentos e atualiza os valores do cliente e do contrato. As regras de cálculo e baixa serão detalhadas posteriormente.

## Protocolo atual de envio e processamento

1. O cobrador envia um lote de movimentações em JSON.
2. O servidor grava o lote pai e seus itens e devolve o ID do lote, ainda antes da autorização para processar.
3. O aplicativo grava esse ID em cada parcela enviada e bloqueia essas parcelas para novo envio.
4. Somente depois de persistir essa informação localmente, o aplicativo envia o comando autorizando o processamento do lote.
5. O servidor processa os pagamentos e as atualizações correspondentes, informa a conclusão ao aplicativo e marca o processamento. A localização exata das flags entre servidor e aplicativo será detalhada.
6. O cobrador pode continuar trabalhando enquanto esse ciclo acontece; novas marcações ficam para um lote posterior.
7. Ao tentar enviar novamente, se já houver um lote registrado no aplicativo, ele consulta a API para verificar se esse lote foi processado.
8. Se ainda não foi processado, solicita o processamento e retoma o mesmo rito.
9. Novas parcelas marcadas só seguem em outro lote depois do processamento do lote anterior.

O bloqueio local de reenvio após receber o ID não deve ser presumido como equivalente aos campos de bloqueio de negócio no servidor; a relação precisa ser confirmada.

## Lote sem vínculo com o aplicativo e recuperação pelo web

Regra esclarecida pelo usuário: se o servidor gravou o lote, mas o aplicativo não recebeu/persistiu seu ID, esse lote fica sem ligação com o aplicativo e não será processado automaticamente. Na nova tentativa, grava-se um novo lote, que segue o rito normal de confirmação e autorização. Não é necessário reutilizar o lote sem vínculo nesse fluxo.

- Preservar o lote sem vínculo e seus itens no servidor para consulta e eventual recuperação.
- Construir um módulo no sistema web principal para visualizar os lotes e seus itens, inclusive os sem vínculo, com ações administrativas a detalhar.
- A ação explicitamente solicitada é o processamento manual de um lote, por exemplo para recuperar recebimentos quando o cobrador apagou acidentalmente os dados do aplicativo.
- A restrição de aguardar o processamento do lote anterior refere-se ao lote vinculado no aplicativo; o lote sem vínculo não deve impedir a criação do novo lote descrita acima.

Ponto técnico para detalhar: antes da recuperação manual, verificar se as mesmas movimentações já foram processadas em outro lote. O fato de o lote antigo não ter sido processado não garante que seus recebimentos não tenham sido reenviados e baixados em um lote novo. Definir também como identificar a perda do vínculo, autorizar a ação manual e registrar quem a realizou. Essas são definições de implementação pendentes, não ações já existentes no módulo web.

## Exemplo de baixa mostrado nas novas telas

As duas capturas adicionais mostram a digitação de um recebimento de R$ 1.850,00 e o resultado distribuído entre parcelas:

| Parcela | Valor exibido antes | Valor marcado para recebimento |
| --- | --- | --- |
| 4 | R$ 1.050,00 | R$ 1.050,00 |
| 5 | R$ 1.050,00 | R$ 800,00 |
| 6, 7 e 8 | R$ 1.050,00 cada | Não marcadas |

O total marcado é R$ 1.850,00. Nesse exemplo, a parcela 4 recebe o valor integral e a parcela 5 recebe parcialmente, restando R$ 250,00 de seu valor anterior, antes de eventuais ajustes de cálculo. O valor de R$ 800,00 mostrado na linha é o valor destinado ao recebimento, não o saldo restante de R$ 250,00. A tela mantém a ação Confirmar e as coordenadas GPS.

As imagens indicam distribuição sequencial do valor digitado nesse exemplo. A regra geral de ordenação, a possibilidade de alterar a seleção e o tratamento de valores superiores ao saldo total ainda precisam ser confirmados; não inferir essas regras apenas a partir das telas.

## Estado visual de envio por parcela

Uma captura adicional enviada pelo usuário mostra a parcela 20 com o ícone de envelope e confirmação verde, correspondente à legenda **Enviado**. As parcelas seguintes aparecem sem marcação. A tela também exibe dias de atraso em vermelho.

- A legenda distingue **Marcar**, **Enviado** e **Erro**.
- Conforme esclarecimento do usuário, **Enviado na caixa significa parcela bloqueada no aplicativo**. O bloqueio afeta somente aquela parcela; o cobrador pode continuar recebendo as demais parcelas, inclusive do mesmo contrato.
- A parcela enviada permanece bloqueada e sua situação local só é atualizada quando a carteira é baixada novamente. A confirmação de processamento do lote não libera por si só essa parcela no aplicativo.
- Essa regra também se aplica ao recebimento parcial: enquanto a parcela estiver enviada/bloqueada, não há novo recebimento nela até a atualização pela nova carga da carteira.
- O ícone Enviado, isoladamente, não comprova que o servidor já processou a baixa. O comportamento visual em caso de erro ainda será detalhado pelo usuário.

## Indicadores de visita na lista e nos contratos

- O usuário confirmou que a **mãozinha vermelha para baixo significa Não pagou**, uma ocorrência de cobrança.
- Na captura dos contratos, o contrato 00276 aparece com uma confirmação verde, enquanto os contratos 00327 e 00340 aparecem com a mãozinha vermelha para baixo. Isso mostra indicadores distintos por contrato de um mesmo cliente.
- Na lista de clientes, uma linha aparece com confirmação verde e outra com o carimbo **Fechado**. Preservar a identificação visual de Fechado como ocorrência.
- Esclarecimento em 20/10/2026: a confirmação verde no cliente exige resposta a todos os seus contratos e pagamento em todos. Se algum contrato recebeu “Não pagou”, apresentar a mãozinha vermelha para baixo. “Fechado” vale para todos os contratos. Esses indicadores não significam quitação integral nem processamento do lote.
- A ocorrência Não pagou é distinta da situação financeira de atraso/vencimento: as telas exibem separadamente o indicador da visita e os totais de parcelas e valores em atraso.

## Composição da base e validação do funcionário

Complemento informado pelo usuário:

- A carga atual usa consultas com INNER JOIN para selecionar parcelas com dados do contrato, além de trazer os clientes.
- Após autenticar na API, também é carregado o cadastro do usuário para uso local.
- O usuário descreve o download como trazer o banco completo. Pelo contexto, há seleção prévia dos dados da carteira; não assumir que isso significa copiar todo o banco da empresa. O conjunto exato de tabelas ainda será detalhado.
- No envio, o login é verificado novamente na API. Se o funcionário tiver sido bloqueado, não consegue enviar novas movimentações. Preservar essa regra relatada.

Orientação de arquitetura para avaliar: continuar entregando um arquivo SQLite completo, mas contendo somente os dados necessários ao cobrador e ao funcionamento offline. Não é obrigatório replicar todo o cadastro do usuário ou todas as tabelas do servidor. Selecionar os campos locais conforme as telas e regras, sem incluir senha ou hash de senha do servidor.

A validação no envio deve consultar a situação atual do funcionário e seu vínculo com o tenant no servidor; a cópia local do cadastro não comprova autorização atual. O bloqueio remoto só pode ser conhecido pelo aparelho quando houver comunicação com a API. Se o envio for recusado, preservar as movimentações locais pendentes. O procedimento administrativo para recuperá-las ainda precisa ser definido: um lote que nunca chegou ao servidor não estará disponível para recuperação no módulo web de lotes.

## Tecnologia proposta: Flutter e SQLite

O usuário autorizou iniciar a criação do aplicativo Flutter em `D:\PROJETOINI\APP`.

Base inicial criada em 19/10/2026: projeto Android Flutter, menu em português, inicialização do SQLite local para confirmações pendentes de download e fluxo de confirmação modelado por interfaces. Análise estática sem problemas e cinco testes aprovados. Ainda não há integração real com a API, extração/instalação da carteira ou telas operacionais de cobrança. O SDK Flutter está em `D:\PROJETOINI\flutter-sdk`; o Android SDK não foi encontrado pelo `flutter doctor`, portanto ainda não foi gerado APK nem validada execução em aparelho.

### Exclusão do ZIP após download

Requisito explícito: após baixar o ZIP da carteira, apagar esse arquivo no servidor. Proposta de protocolo: o aplicativo confirma o recebimento completo e a validação do arquivo; a API então exclui somente o artefato associado àquela carga, tenant e usuário autenticados. Não excluir ao iniciar a transmissão, pois uma interrupção deixaria o aplicativo sem o arquivo completo. A confirmação deve poder ser repetida sem erro se o arquivo já foi removido. Prever expiração dos arquivos abandonados quando a confirmação não chegar. As rotas e a implementação no servidor ainda precisam ser construídas.

### Endereço de produção e seleção da empresa

O usuário deseja gerar o APK no ambiente de desenvolvimento para consumir o servidor Ubuntu e indicou `https://cvfinanceiro.vstec.net`. Deseja selecionar a empresa pelo código informado no aplicativo.

Verificação do código local: `app/tenancy/middleware.py` já aceita `company_code` no formulário de login, mas rejeita códigos de outra empresa quando o domínio está vinculado a um tenant. A documentação de implantação vincula `cvfinanceiro.vstec.net` à CV. Portanto, esse endereço não é intercambiável entre empresas na configuração documentada. O estado efetivo do servidor não foi consultado.

Para um endereço único do aplicativo, o mecanismo existente permite um host neutro em `TENANT_API_HOSTS`, sem vínculo a uma empresa no registro, com DNS, proxy e TLS configurados. Nesse host, o código seleciona a empresa no login e o `tenant_id` do token mantém o vínculo nas próximas requisições. Adicionar um domínio já vinculado a CV em `TENANT_API_HOSTS` não remove a verificação de divergência. O domínio neutro de produção ainda precisa ser definido/configurado; não alterar a proteção de isolamento entre domínios apenas para aceitar códigos diferentes.

Atualização: o usuário apontou `api.vstec.net`, adotado como domínio neutro. DNS verificado: `46.62.156.67`. Configuração de URL e permissão de internet preparadas no APP; roteiro e virtual host preparados em [app-dominio-producao.md](app-dominio-producao.md). Não houve implantação remota, e o HTTPS ainda não foi validado. A URL base configurada é `https://api.vstec.net/api/v1`.

Atualização posterior em 19/10/2026: o usuário configurou o servidor em `/var/www/apicontratos/ContratosN/API`, usando `docker-compose.yml` e `docker-compose.tenant.yml`. Corrigiu o bloco HTTPS que estava retornando 444, habilitou `TENANT_API_HOSTS=api.vstec.net`, recriou a API e recarregou os proxies `web` e `tenant-web`. O domínio passou a responder HTTP 200 com `{"status":"ok"}`, também confirmado deste ambiente. Empresas existentes mencionadas na implantação: CV, MS e BC.

O aplicativo recebeu login por formulário (`company_code`, `username`, `password`), consulta autenticada de `/auth/me`, identificação do usuário/empresa no menu e saída de sessão. Nesta etapa os tokens ficam apenas em memória, sem senha persistida; retomada offline e refresh automático ainda estão pendentes. A API atual exige permissão `acesso_web`, além de usuário ativo; essa regra não foi alterada. Vinte testes automatizados passaram, incluindo login simulado nas três empresas, recusas e timeout. Ainda não houve login com credenciais reais nem teste em aparelho.

APK release 1.0.0+1 gerado localmente em `D:\PROJETOINI\APP\build\app\outputs\flutter-apk\app-release.apk` (aproximadamente 47,5 MB), configurado para `https://api.vstec.net/api/v1`. Assinatura própria RSA 3072 validada com `apksigner verify` (esquema v2). SHA-256 do APK: `5e767f0228bc15c2dd90c2cdf274ee829b2ae3013fcb6fa1408ece1e5402c9f4`. Android SDK instalado em `D:\PROJETOINI\android-sdk`, JDK 21 existente configurado no Flutter. Chave local em `APP/android/signing/cobrador-release.jks` e configuração em `APP/android/key.properties`, ambos ignorados pelo Git. Guardar backup privado desses arquivos para assinar atualizações futuras. O APK permite testar autenticação; não substitui ainda o app operacional de cobrança.

Diretório indicado pelo usuário para o aplicativo: `D:\PROJETOINI\APP`. Na inspeção inicial em 19/10/2026, a pasta existe e está vazia; nenhum projeto Flutter foi criado nesta etapa.

Flutter com SQLite é a alternativa sugerida pelo usuário para substituir o aplicativo WinDev. A proposta é compatível com manter a carteira local e sincronizar os lotes explicitamente. Referências oficiais: https://docs.flutter.dev/cookbook/persistence/sqlite e https://docs.flutter.dev/app-architecture/design-patterns/offline-first.

Sugestão de arquitetura para avaliar, ainda não aprovada: separar o arquivo SQLite da carteira, gerado pela API e substituído no download, de um arquivo SQLite de movimentações locais, contendo recebimentos, ocorrências, solicitações e controle dos lotes. Isso permite renovar a carteira sem sobrescrever o histórico de envio e as movimentações pendentes. A conciliação entre os dois arquivos precisa preservar o bloqueio por parcela e a atualização somente na nova carga, conforme as regras já relatadas.

A API deverá gerar o SQLite no formato e versão de esquema esperados pelo aplicativo. Antes da troca, o aplicativo deve fechar as conexões da carteira e validar o arquivo novo; a política de conciliação de pendências deve ser definida antes de permitir a nova carga.

## Pontos para detalhar antes da implementação

Estes pontos são questões técnicas pendentes, não mudanças aprovadas no fluxo atual:

- Nova tecnologia do aplicativo e formato do banco local.
- Como preservar recebimentos, ocorrências e solicitações pendentes ao substituir a carteira local.
- Como identificar tecnicamente o lote sem vínculo e impedir duplicidade na recuperação manual quando houver reenvio em outro lote, respeitando a regra de criação de um novo lote esclarecida acima.
- Como garantir que repetir o comando de processamento não aplique novamente um pagamento, inclusive em caso de falha durante o processamento.
- Tratamento de lotes parcialmente processados, itens bloqueados e liberação do próximo lote nessas situações.
- Escopo da regra de um lote pendente por vez: aparelho, usuário, ou outra combinação dentro do tenant.
- Tratamento de pagamento parcial, múltiplos recebimentos na mesma parcela e mudanças de saldo no servidor enquanto o aparelho está offline.
- Tratamento de GPS indisponível e origem/fuso das datas e horas.
- Significado distinto das situações em dias, atrasado e vencido mostradas nas telas atuais.
- Regras das solicitações e dos filtros restantes, todas e fora da lista.

## Referências

### Implementação da carteira em 19/10/2026

Correção em 20/10/2026: a carteira é filtrada pelo usuário responsável pelo cliente (`clientes.usuario_id`), comparado ao usuário autenticado. O filtro anterior por vendedor do contrato (`usuario_id_vendedor`) estava incorreto. Implementados geração do SQLite/ZIP, download autenticado, confirmação idempotente de exclusão e expiração de artefatos. No Flutter, implementados validação e instalação, consulta de clientes/contratos/parcelas com observações, sessão segura para reabertura offline e repetição de confirmações pendentes. APK 1.1.0+2 gerado com a mesma chave da versão anterior. Validação local: 25 testes Flutter, 16 testes Python (carteira e tenancy), análise estática sem problemas. A API precisa ser implantada no Ubuntu antes do teste real do download; nenhuma alteração remota foi aplicada. Detalhes em [app-carteira-sqlite.md](app-carteira-sqlite.md).

Relato do usuário e 12 capturas de tela do aplicativo atual, enviadas nesta conversa, com nomes iniciados por `WhatsApp Image 2026-10-19 at 13.41.`. As imagens foram usadas como referência visual; não foram copiadas para o repositório.

Complemento: relato sobre lotes sem vínculo e módulo web, acompanhado das capturas `WhatsApp Image 2026-10-19 at 14.09.23.jpeg` e `WhatsApp Image 2026-10-19 at 14.09.24.jpeg`, mostrando a distribuição de R$ 1.850,00 entre duas parcelas. Essas imagens também não foram copiadas para o repositório.
