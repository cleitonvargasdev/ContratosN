# Clientes e consolidado — ordem de visitas

Origem: terceiro print enviado pelo usuário em 20/10/2026.
Arquivo previsto: `clientes.png` nesta pasta, ainda pendente de cópia.

## Regras confirmadas pelo usuário

Esta tela apresenta os clientes e seu consolidado. O cobrador pode reorganizar a posição dos clientes na lista para definir sua ordem de visitas.

| Visão | Significado |
| --- | --- |
| Restando | Clientes que o cobrador ainda precisa visitar. |
| Todas | Clientes visitados e não visitados da lista de visitas. |
| Fora da lista | Clientes com vencimento amanhã ou em datas futuras, que não precisam ser visitados agora, mas devem estar disponíveis caso entrem em contato para pagar. |

“Fora da lista” não significa excluir o cliente da carteira local. Esses clientes precisam continuar acessíveis para consulta e recebimento.

O estado de visita é diferente do estado de pagamento: não assumir que visitar implica receber ou quitar parcelas.

## Elementos observados

- Campo de pesquisa no topo: “DIGITE AQUI PARA PESQUISAR”.
- Lista vertical de clientes, com um item destacado em azul claro.
- Cada item apresenta nome, endereço, bairro/localidade, campos de contato, quantidade de contratos, turno de cobrança, parcelas em atraso e valor consolidado.
- Nomes em vermelho, valores em azul e quantidade de parcelas atrasadas em vermelho.
- Ação “SALVAR ORDEM LISTA” abaixo dos clientes.
- Controles com setas para cima e para baixo no lado direito.
- Acessos inferiores “RESTANTE”, “TODAS” e “FORA LISTA”.

Os controles são consistentes com a reorganização explicada pelo usuário, mas o gesto exato para selecionar e mover um cliente não está demonstrado no print.

## Direção visual solicitada

O usuário quer uma apresentação mais moderna, preservando o modelo operacional. A imagem é referência de informações e comportamento, não uma exigência de reprodução visual literal.

Proposta para a implementação, ainda não validada visualmente:

- Pesquisa no topo e três filtros com nomes claros: “Restando”, “Todas” e “Fora da lista”.
- Cartões com hierarquia legível: nome, endereço, situação da visita e resumo financeiro.
- Quantidades de contratos e parcelas atrasadas apresentadas de forma compacta.
- Modo explícito de organizar visitas, com arrastar e soltar e alternativa acessível para mover posições.
- Confirmação clara de que a ordem foi salva e preservada para uso offline.

## Pontos a definir antes de implementar as regras

- Qual ação marca uma visita como realizada e quando essa marcação é reiniciada.
- Se a ordem é mantida entre dias e entre downloads da carteira.
- Como mudanças na ordem se comportam quando há pesquisa ou filtro ativo.
- Qual é a composição do campo “VALOR”: total em aberto, total vencido ou outro consolidado.
- Como tratar clientes que possuem simultaneamente parcelas vencidas e futuras.

A disponibilidade de parcelas futuras já faz parte da carga da carteira; a separação visual entre a lista de visitas e “Fora da lista” ainda precisa ser implementada.

Consultar o [documento de migração](../app-cobrador-migracao.md) para as demais regras operacionais.

A [referência do grid após marcações](clientes-marcados.md) mostra confirmação verde e carimbo “Fechado” junto ao consolidado financeiro.

Esclarecimento de 20/10/2026: verde exige resposta e pagamento em todos os contratos; qualquer “Não pagou” aparece com mãozinha vermelha; “Fechado” responde todos os contratos. No desenvolvimento, a visita é considerada completa somente após todos os contratos receberem resposta. O reinício diário ainda não foi definido.
