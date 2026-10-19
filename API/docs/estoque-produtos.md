# Estoque de produtos

O quadro do produto apresenta novos, usados e total. Os saldos só mudam por movimentação; o cadastro não permite sobrescrevê-los.

- **Dar entrada:** estoque inicial, compra ou outros; informar condição, quantidade e observação.
- **Dar baixa:** quebra, extravio, furto/roubo, desgaste, descarte ou outros. Não permite quantidade superior ao saldo da condição escolhida.
- **Ajustar estoque:** informar a quantidade física contada de novos ou usados. O sistema apresenta e registra a diferença. Se o saldo tiver sido movimentado desde a leitura, a operação é recusada até nova conferência.
- **Venda:** salvar os itens do comodato e usar **Confirmar venda e dar saída**. A confirmação preserva os itens e desconta cada condição. Sem a flag do produto, saldo insuficiente impede a venda inteira. Com a flag, o saldo da condição pode ficar negativo.
- **Devolução:** no item de uma venda confirmada, usar **Devolver**, informar a quantidade recebida e a condição (usado por padrão). Aceita devoluções parciais até o limite vendido. Esta entrada não recalcula parcelas ou valores financeiros.
- **Quitação/cancelamento:** não geram entrada automática. O recebimento físico deve ser registrado por devolução.

O histórico registra usuário, data, condição, quantidade, saldo anterior/posterior, motivo e observação. Movimentos de venda/devolução referenciam o item original. Produtos com histórico devem ser inativados, não excluídos. Contratos com venda confirmada não podem ter seus itens apagados.

## Consistência

Venda, saldos e histórico são gravados na mesma transação. Os bloqueios seguem a ordem contrato → produtos em ordem de ID. Entradas, baixas, ajustes e devoluções usam chave de operação para impedir duplicidade por reenvio; confirmação de venda é idempotente por contrato. As versões do comodato e do estoque impedem confirmar dados que foram alterados durante a conferência.

As rotas de estoque usam as permissões existentes de leitura/alteração de produtos. Confirmar venda usa a permissão de alteração de contratos.

## Migração

A revisão `20261019_0051` importa o saldo antigo como **novo**, com movimento de estoque inicial, e inicia usados em zero. É necessário conferir a distribuição física entre novos e usados pelo ajuste. Comodatos anteriores são identificados como legado e preservados como vendas já confirmadas, sem uma nova saída. Eles continuam aceitando devoluções.

Para outros ambientes, executar `python -m scripts.migrate_databases` usando a configuração daquele ambiente. No modo multitenant, o comando migra os bancos das empresas ativas.

## Verificação

- `python -m pytest -q tests/test_stock.py`: saldos, histórico, devolução parcial, idempotência, ajustes desatualizados e rollback integral da venda.
- `tests/test_stock_postgres.py`: teste opcional com cluster PostgreSQL temporário; valida migração do legado, disputa pela última unidade e reenvios concorrentes. Requer `RUN_POSTGRES_INTEGRATION=1` e `POSTGRES_BIN` apontando para os executáveis locais.
- Frontend: `npm run build`.
