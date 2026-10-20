# Grid de clientes após marcações

Origem: print enviado pelo usuário em 20/10/2026, identificado como “aspecto do grid depois de marcados”.
Arquivo previsto: `clientes-marcados.png`, ainda pendente de cópia.

## Elementos observados

- A lista mantém pesquisa, dados consolidados, ordenação e os filtros de visitas.
- Um cliente apresenta uma confirmação verde grande à direita.
- Outro apresenta o carimbo vermelho “FECHADO”.
- Ambos continuam exibindo quantidade de contratos, parcelas em atraso e valor consolidado.
- O cliente com confirmação verde ainda apresenta parcelas em atraso e valor financeiro. O indicador não deve ser interpretado como ausência de dívida.

## Orientação para o novo grid

Preservar indicadores distintos de resultado da visita na apresentação moderna:

- Confirmação verde quando todos os contratos do cliente receberam resposta e todos tiveram pagamento, conforme esclarecimento do usuário em 20/10/2026.
- Mãozinha vermelha para baixo quando algum contrato recebeu a resposta “Não pagou”.
- Identificação explícita de “Fechado”, como ocorrência do cliente.
- Resumo financeiro separado do indicador de visita.
- Texto junto aos ícones para não depender somente de cor.

“Fechado” deve ser registrado para todos os contratos do cliente. A confirmação verde representa recebimento em todos os contratos, não necessariamente quitação integral de seus saldos nem processamento do lote no servidor.

Critério adotado para “Restando”: o cliente permanece enquanto algum contrato ainda não tiver resposta. Um atendimento parcial não deve desaparecer da rota.

Esta captura complementa a [lista de clientes e ordem de visitas](clientes.md) e a seção “Indicadores de visita na lista e nos contratos” do [documento de migração](../app-cobrador-migracao.md).
