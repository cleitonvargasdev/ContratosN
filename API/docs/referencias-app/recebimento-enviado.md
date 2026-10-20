# Recebimento — estado após envio

Origem: print enviado em 20/10/2026, identificado como tela depois de enviar.
Arquivo previsto: `recebimento-enviado.png`, ainda pendente de cópia.

## Elementos observados

A tela de parcelas apresenta a primeira parcela visível com envelope e confirmação verde na coluna “Marcar”, correspondente à legenda “Enviado”. As demais parcelas permanecem sem marcação. Há também as legendas “Marcar” e “Erro” e os dias de atraso em vermelho.

## Regras preservadas do relato de 19/10/2026

As regras abaixo já estavam registradas no [documento de migração](../app-cobrador-migracao.md), nas seções “Protocolo atual de envio e processamento”, “Lote sem vínculo com o aplicativo e recuperação pelo web” e “Estado visual de envio por parcela”.

- “Enviado” significa parcela bloqueada no aplicativo, não comprovação de baixa processada no servidor.
- Somente a parcela enviada fica bloqueada; as demais, inclusive do mesmo contrato, continuam disponíveis para recebimento.
- Mesmo um recebimento parcial bloqueia a parcela até baixar uma nova carteira.
- A confirmação de processamento do lote não libera a parcela local. A situação é atualizada pela nova carga.
- A API grava lote e itens e devolve o ID. O app persiste o ID nas parcelas e as bloqueia antes de autorizar o processamento.
- Antes de enviar novas marcações em outro lote, o app consulta e resolve o processamento do lote anterior vinculado.
- O cobrador pode continuar trabalhando enquanto isso; novas marcações aguardam o lote seguinte.
- Se o servidor gravar um lote mas o app não receber/persistir o ID, esse lote fica sem vínculo e não é processado automaticamente. Uma nova tentativa cria outro lote.
- O lote sem vínculo permanece disponível para consulta e eventual recuperação manual no web, com verificação contra baixa duplicada antes de processar.
- No envio, a API revalida o funcionário. Uma recusa deve preservar os movimentos locais pendentes.

O comportamento visual e operacional da legenda “Erro” ainda não está definido.
