"""Estoque por condição e movimentos auditáveis.

Revision ID: 20261019_0051
Revises: 20261015_0050
"""
from alembic import op
import sqlalchemy as sa

revision = "20261019_0051"
down_revision = "20261015_0050"
branch_labels = None
depends_on = None


def upgrade():
    for name in ("estoque_novos", "estoque_usados", "estoque_versao"):
        op.add_column("produtos", sa.Column(name, sa.Integer(), nullable=False, server_default="0"))
    op.add_column("produtos", sa.Column("permite_vender_sem_estoque", sa.Boolean(), nullable=False, server_default=sa.false()))
    for name in ("venda_confirmada", "estoque_legado"):
        op.add_column("contratos_comodatos", sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos_comodatos", sa.Column("versao", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("contratos_comodato_itens", sa.Column("condicao", sa.String(10), nullable=False, server_default="novo"))
    op.add_column("contratos_comodato_itens", sa.Column("quantidade_devolvida", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "estoque_movimentos",
        sa.Column("movimento_id", sa.Integer(), primary_key=True),
        sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produtos.produto_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("contratos_comodato_itens.item_id", ondelete="RESTRICT")),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("usuario_nome", sa.String(120), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("condicao", sa.String(10), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("saldo_antes", sa.Integer(), nullable=False),
        sa.Column("saldo_depois", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(60), nullable=False),
        sa.Column("observacao", sa.Text()),
        sa.Column("operacao_id", sa.String(100), nullable=False),
        sa.Column("assinatura", sa.String(64), nullable=False),
        sa.UniqueConstraint("produto_id", "operacao_id", name="uq_estoque_operacao_produto"),
        sa.CheckConstraint("condicao IN ('novo', 'usado')", name="ck_estoque_condicao"),
        sa.CheckConstraint("saldo_depois = saldo_antes + quantidade", name="ck_estoque_saldo"),
    )
    op.create_index("ix_estoque_movimentos_produto_id", "estoque_movimentos", ["produto_id"])
    op.create_index("ix_estoque_movimentos_item_id", "estoque_movimentos", ["item_id"])
    op.execute("UPDATE produtos SET estoque_novos = COALESCE(estoque, 0), estoque = COALESCE(estoque, 0)")
    op.execute("""INSERT INTO estoque_movimentos
        (produto_id, usuario_nome, tipo, condicao, quantidade, saldo_antes, saldo_depois, motivo, observacao, operacao_id, assinatura)
        SELECT produto_id, 'Migração', 'entrada', 'novo', estoque_novos, 0, estoque_novos,
        'Estoque inicial', 'Saldo anterior importado como novo. Conferir novos e usados no inventário.',
        'migracao-inicial', 'migracao-inicial' FROM produtos WHERE estoque_novos <> 0""")
    # Existing contracts do not establish whether stock was physically counted before or after sale.
    # Preserve the current balance; never infer another outgoing movement for historical contracts.
    op.execute("UPDATE contratos_comodatos SET venda_confirmada = true, estoque_legado = true")


def downgrade():
    op.drop_table("estoque_movimentos")
    for name in ("quantidade_devolvida", "condicao"):
        op.drop_column("contratos_comodato_itens", name)
    for name in ("versao", "estoque_legado", "venda_confirmada"):
        op.drop_column("contratos_comodatos", name)
    for name in ("permite_vender_sem_estoque", "estoque_versao", "estoque_usados", "estoque_novos"):
        op.drop_column("produtos", name)
