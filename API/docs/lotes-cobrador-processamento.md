# Lotes do cobrador: envio, processamento, bloqueio e ocorrências

## Regra vigente — 21/10/2026

Este documento registra as decisões confirmadas para substituir as anotações
anteriores sobre processamento manual e preservação de lote sem vínculo no
aplicativo. O lote é criado e persistido primeiro no servidor; o aplicativo
somente autoriza sua execução depois de gravar localmente o ID devolvido pela
API e bloquear as parcelas envolvidas.

## Objetivos

- Permitir que o cobrador trabalhe offline e envie recebimentos, ocorrências e
  solicitações em lote.
- Impedir novo recebimento local da mesma parcela enquanto ela estiver em um
  lote aceito pelo servidor.
- Processar cada item isoladamente: uma falha não cancela os demais itens.
- Bloquear a carteira do cobrador quando qualquer item exigir conferência
  humana, sem desfazer os itens já processados com sucesso.
- Manter trilha de auditoria de lote, item, localização, horário do aparelho,
  data do servidor, falha e desbloqueio administrativo.

## Entidades persistidas no servidor

### Lote pai

Representa um envio do cobrador, dentro de um tenant. Deve conter, no mínimo:

| Campo | Regra |
| --- | --- |
| `id` | ID devolvido ao aplicativo após a persistência do lote. |
| `tenant_id`, `cobrador_id` | Identificam empresa e cobrador responsável. |
| `chave_idempotencia` | Identidade única do envio originado no aparelho. |
| `criado_em_servidor` | Auditoria técnica do servidor. |
| `status` | `criado`, `processando`, `processado` ou `bloqueado`. |
| `bloqueado` | Verdadeiro quando algum item exigir análise. |
| `motivo_bloqueio` | Primeiro ou resumo dos motivos que bloquearam o lote. |
| `executado_em`, `finalizado_em` | Auditoria da execução. |
| `desbloqueado_por`, `desbloqueado_em`, `motivo_desbloqueio` | Auditoria obrigatória da liberação web. |

O lote pai não é apagado pelo fluxo normal depois de iniciado ou processado.

### Itens filhos de recebimento

Cada parcela recebida gera um item filho com contrato, parcela, valor,
principal, juros, GPS, hora do celular, data do servidor e estado do
processamento. Deve registrar também:

| Campo | Regra |
| --- | --- |
| `processado` | Verdadeiro somente após a baixa financeira ser concluída. |
| `bloqueado` | Verdadeiro se o item não puder ser aplicado automaticamente. |
| `motivo_bloqueio` | Motivo técnico e legível da falha. |
| `recebimento_id` | Referência ao recebimento efetivamente criado, quando houver. |
| `tentativas`, `processado_em` | Auditoria e repetição segura. |

### Ocorrências

Não existe atualmente uma tabela/modelo de ocorrências na API; ela deve ser
criada. Cada ocorrência é independente da baixa financeira e deve armazenar:

- tipo: `nao_pagou` ou `fechado`;
- tenant, cobrador, cliente e contrato; `fechado` é gravado para todos os
  contratos do cliente conforme a regra já adotada no app;
- latitude, longitude e situação do GPS (`capturado` ou `timeout`);
- `hora_celular`, recebida do aparelho;
- `data_servidor`, sempre atribuída pelo servidor e nunca pelo cobrador;
- data/hora técnica de criação no servidor e referência ao lote pai.

Ocorrência não deve ser tratada como quitação, cancelamento ou alteração do
saldo da parcela.

## Fluxo obrigatório do aplicativo e da API

1. O aplicativo agrupa operações ainda não enviadas e gera uma
   `chave_idempotencia` única para o envio.
2. O aplicativo envia o lote para a API. A API persiste, em uma transação, o
   lote pai, todos os filhos de recebimento e as ocorrências; então devolve o
   `lote_id`.
3. O aplicativo persiste o `lote_id` e bloqueia localmente todas as parcelas
   de recebimento pertencentes ao lote. O bloqueio local evita novo lançamento
   para a mesma parcela, mas não é o bloqueio administrativo de negócio.
4. Somente depois da etapa 3 confirmada no SQLite do aparelho, o aplicativo
   chama a execução do lote no servidor.
5. A execução é idempotente pelo `lote_id`: repetir a chamada deve retomar ou
   consultar o mesmo lote, jamais gerar nova baixa.
6. O servidor executa os itens filhos um por um. Para cada êxito, cria o
   recebimento, aplica a baixa e atualiza os valores da parcela, do contrato e
   do cliente na mesma transação do item.
7. Se um item falhar, ele recebe `bloqueado=true` e o motivo. O lote pai recebe
   `bloqueado=true` e `status=bloqueado`, mas a execução continua nos demais
   itens.
8. Ao final, a API devolve o resumo por item. O app remove/desbloqueia somente
   as operações que foram processadas com sucesso; itens bloqueados ficam
   rastreáveis pelo lote e a carteira do cobrador permanece impedida de baixar
   nova carga até a liberação administrativa.

## Exemplos de bloqueio

- O cliente quitou a parcela na loja depois que o cobrador baixou a carteira e
  também recebeu esse valor no percurso. O item do cobrador não pode quitar
  novamente: fica bloqueado com o motivo de parcela já quitada. Os demais itens
  do lote continuam sendo processados.
- Um contrato foi excluído após a carteira ser baixada e antes do recebimento
  do cobrador. O item fica bloqueado com o motivo de contrato inexistente; os
  demais itens continuam sendo processados.

Outros conflitos financeiros devem seguir a mesma regra: não aplicar baixa
duplicada, conservar o item e o motivo, bloquear o lote/cobrador e continuar
os itens independentes.

## Bloqueio da carteira e desbloqueio web

Enquanto houver lote bloqueado para o cobrador no tenant, a API deve recusar a
geração ou o download de nova carteira para esse cobrador. A tela de
**Desbloqueio** no sistema web deve:

1. listar os lotes bloqueados;
2. permitir abrir um lote e visualizar cobrador, contrato, parcela, valor,
   item filho, motivo do bloqueio e situação de cada item;
3. permitir o ajuste manual necessário fora do lote, quando aplicável;
4. exigir motivo para desbloquear;
5. registrar usuário administrativo e data/hora do desbloqueio;
6. liberar o próximo download de carteira do cobrador sem apagar histórico do
   lote e de seus itens.

O desbloqueio não deve reprocessar automaticamente o item filho bloqueado.

## Quedas de conexão e recuperação

### A API criou o lote, mas o app não recebeu ou não gravou o ID

Antes de fazer a primeira chamada, o app gera e grava localmente a
`chave_idempotencia` do lote. Se a resposta se perder, ele repete o **mesmo**
`POST` com a mesma chave; a API devolve o mesmo `lote_id`, sem criar filhos ou
recebimentos duplicados. Portanto um novo lote nunca deve apagar às cegas um
lote anterior do cobrador.

Uma rotina futura de limpeza poderá remover somente lotes realmente abandonados
em `criado`, sem solicitação de execução e depois do prazo de retenção. Nunca
deve remover lotes `processando`, `processado` ou `bloqueado`.

### O app gravou o ID e bloqueou as parcelas, mas falhou ao autorizar execução

Ao abrir Transmissão ou tentar reenviar, o app consulta o `lote_id` no servidor:

- se estiver `criado`, chama novamente a execução do mesmo lote;
- se estiver `processando`, consulta até receber o resultado, sem criar lote
  novo;
- se estiver `processado` ou `bloqueado`, aplica o resultado por item no
  SQLite local;
- se o lote não existir, somente então libera as operações locais para formar
  novo lote, registrando o evento para auditoria.

Assim, uma perda de resposta depois do comando de execução não produz dupla
baixa e não deixa o lote sem caminho de recuperação.

## Solicitações

Solicitações também devem usar fila local e chave idempotente. A API já possui
rota de solicitações; falta completar no app o estado por item (`pendente`,
`enviando`, `enviado`, `falhou`), reenvio seguro e a remoção local somente após
confirmação da criação no servidor. Solicitações não entram na baixa financeira
do lote de recebimentos, mas podem compartilhar a mesma tela de transmissão e
o mesmo mecanismo de fila.

## Critérios de aceite para implementação

- Repetir criação ou execução não duplica lote, ocorrência ou recebimento.
- Conflito em uma parcela bloqueia o lote/cobrador, preserva motivo e não
  impede os outros itens válidos.
- Nova carteira é recusada para cobrador com lote bloqueado.
- Administrador visualiza e desbloqueia lote com auditoria.
- Datas de operação vêm do servidor; horas de visita vêm do aparelho.
- GPS e ocorrências são persistidos mesmo quando não houver pagamento.
- Em qualquer queda de conexão, o app consegue retomar pelo `lote_id` ou criar
  novo lote após a limpeza limitada dos lotes apenas `criado`.
