# Recebimento e ocorrência por contrato

Origem: quinto print enviado pelo usuário em 20/10/2026.
Arquivo previsto: `recebimento-contrato.png` nesta pasta, ainda pendente de cópia.

## Regras confirmadas pelo usuário

Nesta tela, o cobrador registra que o contrato não teve pagamento ou informa quanto recebeu.

- Pode selecionar parcelas pelas caixas de marcação.
- Pode digitar um valor no campo superior para que o aplicativo distribua o recebimento entre as parcelas.
- Pode editar diretamente o valor de uma parcela, inclusive informando um valor maior que o valor da parcela.
- O excedente informado diretamente na parcela representa juros. Não limitar esse campo ao valor da parcela nem redistribuir automaticamente esse excedente para outra parcela.
- O exemplo de R$ 1.050,00 é um dado da captura, não um valor fixo.

## GPS — requisito e proposta do usuário

As coordenadas GPS são obrigatórias no fluxo operacional. O usuário propõe uma exceção: com GPS ligado, tentar obter a localização por até 30 segundos; se não conseguir, permitir continuar sem coordenadas.

Registrar essa proposta como regra a detalhar na implementação:

1. Solicitar a localização para o registro da operação.
2. Com o serviço de localização ligado e acesso permitido, aguardar a obtenção por no máximo 30 segundos.
3. Se obtiver a posição, associá-la à operação.
4. Se o prazo acabar sem posição, permitir continuar com latitude e longitude ausentes.

Não preencher coordenadas ausentes com zero nem reutilizar silenciosamente uma posição antiga como se fosse a posição desta operação. Sugestão técnica: registrar também o motivo da ausência (`timeout`) e o horário da tentativa, para distinguir a exceção de uma coleta bem-sucedida.

A exceção proposta não define o comportamento com GPS desligado ou permissão negada. Não ampliar automaticamente a dispensa para esses casos.

## Elementos observados

- Nome do cliente no topo.
- Legendas “MARCAR”, “ENVIADO” e “ERRO”.
- Campo superior “DIGITAR VALOR”, com botão de ícone monetário.
- Tabela de parcelas com colunas “PARC.”, “VENCTO”, “ATRASO”, “VALOR” e “MARCAR”.
- Valor editável e caixa de seleção em cada linha.
- Botão vermelho “NÃO PAGOU”.
- Campo inferior acompanhado de “R$”; sua função exata ainda não foi explicada.
- Botão “ATUALIZAR MEU LOCAL” e campos de latitude e longitude.
- Botões inferiores “VOLTAR” e “CONFIRMAR”.

## Orientação para a construção

- Preservar os três caminhos: marcar parcelas, distribuir valor total e editar recebimento por parcela.
- Tornar explícitos os valores destinados à parcela e aos juros antes da confirmação.
- Usar cálculo monetário com precisão decimal ou unidades inteiras, conforme o padrão do projeto.
- Manter recebimentos e ocorrências disponíveis offline e preservados durante a troca da carteira.
- Tratar o envio em lote e os estados de sincronização conforme as regras do documento de migração.
- Aplicar a coleta de localização às operações financeiras e ocorrências conforme o escopo que for confirmado; não confundir a posição da operação com alteração do endereço do cliente.

## Pontos a definir antes de implementar

- Ordem de distribuição do valor total entre parcelas e tratamento de eventual excedente nesse campo. A regra de juros foi confirmada para a edição direta da parcela.
- Base do cálculo de juros em parcelas parcialmente pagas ou com juros anteriores: valor original, saldo atual ou outro valor.
- Como a marcação da caixa interage com valores digitados e pagamentos parciais.
- “Não pagou” responde o contrato. Critério adotado após esclarecimento de 20/10/2026: o cliente sai de “Restando” somente quando todos os seus contratos tiverem resposta.
- Função do campo inferior “R$”.
- Se a exceção de GPS também vale para “Não pagou” e “Fechado”.
- Precisão aceitável da localização e tratamento de GPS desligado ou permissão negada.

Consultar [contratos do cliente](contratos-cliente.md), [transmissão](transmissao.md) e o [documento de migração](../app-cobrador-migracao.md).

A [referência após envio](recebimento-enviado.md) reúne as regras já registradas sobre bloqueio de parcelas enviadas e processamento dos lotes.
