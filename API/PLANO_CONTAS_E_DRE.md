# Proposta: Plano de Contas e Resultado Mensal

> Documento de decisao. Nao implementa nenhuma alteracao no sistema atual.

## Objetivo

Disponibilizar um relatorio mensal simples para clientes leigos, mostrando o
resultado do mes (lucro ou prejuizo), sem confundir movimentacao de caixa com
lucro.

Exemplo da visao principal:

| Resumo do mes | Valor |
|---|---:|
| Total de receitas | R$ 45.700,00 |
| Total de gastos | R$ 22.500,00 |
| Resultado (lucro do mes) | R$ 23.200,00 |

Tambem pode haver uma aba separada de **Fluxo de caixa**, que considera todo o
dinheiro que entrou e saiu.

## Plano de contas proposto

O menu **Plano de contas** seria a tabela de classificacao dos lancamentos.
Campos sugeridos:

- `id`
- `grupo`
- `tipo` (`credito` ou `debito`)
- `descricao`
- `entra_no_lucro` (`sim` ou `nao`)
- `ativo`

Contas iniciais sugeridas:

| Grupo | Tipo | Entra no lucro? | Descricao |
|---|---|---:|---|
| Receitas de juros | Credito | Sim | Juros recebidos ou apropriados nos contratos. |
| Multas e acrescimos | Credito | Sim | Valores adicionais cobrados por atraso. |
| Receitas de aluguel | Credito | Sim | Recebimentos de contratos de aluguel ou recorrencia. |
| Outras receitas | Credito | Sim | Entradas que nao sejam devolucao de emprestimo. |
| Comissoes pagas | Debito | Sim | Pagamentos de comissoes a vendedores e cobradores. |
| Despesas com funcionarios | Debito | Sim | Salarios, adiantamentos, beneficios e afins. |
| Despesas com fornecedores | Debito | Sim | Servicos, materiais e compras de fornecedores. |
| Despesas administrativas | Debito | Sim | Aluguel, internet, energia, sistemas e escritorio. |
| Impostos e taxas | Debito | Sim | Tributos, tarifas bancarias e taxas. |
| Outras despesas | Debito | Sim | Gastos nao contemplados nas demais categorias. |
| Liberacao de emprestimos | Debito | Nao | Valor entregue ao cliente; reduz o caixa, mas nao e despesa. |
| Recebimento de principal | Credito | Nao | Devolucao do valor emprestado; aumenta o caixa, mas nao e receita. |

## Onde guardar a classificacao

A classificacao deve ser vinculada ao **lancamento financeiro**, e nao ao
relatorio.

| Origem | Proposta |
|---|---|
| Conta a pagar | Adicionar `plano_conta_id` em `contas_pagar`. |
| Pagamento de conta a pagar | Herdar a categoria da conta a pagar. |
| Recebimento de contrato | Classificar automaticamente pela API. |
| Emprestimo liberado | A conta a pagar vinculada ao contrato recebe automaticamente “Liberacao de emprestimos”. |
| Lote de comissoes | A conta a pagar gerada recebe automaticamente “Comissoes pagas”. |

Nas contas a pagar criadas manualmente, o usuario escolheria a categoria. Nas
origens conhecidas, a API preencheria automaticamente.

## Recebimentos lancados pelo APK de cobradores

O cobrador deve informar apenas dados operacionais, por exemplo: contrato ou
parcela, valor, data, desconto e observacao. Ele nao deve escolher uma conta do
plano de contas.

A API deve buscar o contrato e classificar automaticamente:

| Tipo de contrato/valor | Conta sugerida | Entra no lucro? |
|---|---|---:|
| Principal devolvido de emprestimo | Recebimento de principal | Nao |
| Juros, multa ou acrescimo | Receitas de juros / Multas e acrescimos | Sim |
| Contrato de aluguel ou recorrencia | Receitas de aluguel | Sim |

## Modelo recomendado para recebimentos mistos

Uma cobranca pode conter principal e juros. Exemplo: recebimento total de
R$ 115,00, composto por R$ 100,00 de principal e R$ 15,00 de juros. Somar os
R$ 115,00 como receita distorceria o lucro.

Para tratar isso corretamente, a proposta mais robusta e:

- `recebimentos`: cabecalho do lancamento enviado pelo APK;
- `recebimentos_itens`: divisao financeira do recebimento.

Campos sugeridos para `recebimentos_itens`:

- `id`
- `recebimento_id`
- `plano_conta_id`
- `valor`
- `descricao` ou `origem`

A API criaria os itens. No exemplo acima, ela geraria um item de R$ 100,00 em
“Recebimento de principal” e outro de R$ 15,00 em “Receitas de juros”.

## Regra do relatorio

**Resultado do mes (DRE gerencial)**:

`receitas com entra_no_lucro = sim - despesas com entra_no_lucro = sim`

**Fluxo de caixa**:

`todos os recebimentos - todos os pagamentos`

O primeiro responde “quanto lucrei?”; o segundo responde “quanto dinheiro
entrou ou saiu?”.

## Situacao atual do projeto

O sistema ja registra recebimentos em `recebimentos`, pagamentos em
`contas_pagar_pagamentos`, contas a pagar, contratos e comissoes. Ainda nao ha
plano de contas nem a separacao estruturada entre principal e juros dentro de
cada recebimento. Por isso, antes da implementacao, sera necessario decidir se
o resultado sera inicialmente uma visao de caixa simplificada ou se sera
adotado o modelo com itens de recebimento para uma DRE mais correta.
