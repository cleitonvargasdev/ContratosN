"""create planos pagamentos table

Revision ID: 20260404_0012
Revises: 20260404_0011
Create Date: 2026-04-04 22:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0012"
down_revision = "20260404_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "planos_pagamentos",
        sa.Column("planos_id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("descricao", sa.String(length=50), nullable=True),
        sa.Column("qtde_dias", sa.Integer(), nullable=True),
        sa.Column("percent_juros", sa.Float(), nullable=True),
        sa.Column("valor_parcela", sa.Float(), nullable=True),
        sa.Column("valor_base", sa.Float(), nullable=True),
        sa.Column("valor_final", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("planos_id"),
    )
    op.create_index(op.f("ix_planos_pagamentos_planos_id"), "planos_pagamentos", ["planos_id"], unique=False)
    op.create_index(op.f("ix_planos_pagamentos_descricao"), "planos_pagamentos", ["descricao"], unique=False)

    op.execute(
        """
        INSERT INTO perfil_permissoes (perfil_id, resource_key, resource_label, can_read, can_create, can_update, can_delete)
        SELECT p.id, 'planos_pagamentos', 'Planos de Pagamento', true, true, true, true
        FROM perfis p
        WHERE p.nome = 'Administrador'
          AND NOT EXISTS (
            SELECT 1 FROM perfil_permissoes existing
            WHERE existing.perfil_id = p.id AND existing.resource_key = 'planos_pagamentos'
          )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM perfil_permissoes WHERE resource_key = 'planos_pagamentos'")
    op.drop_index(op.f("ix_planos_pagamentos_descricao"), table_name="planos_pagamentos")
    op.drop_index(op.f("ix_planos_pagamentos_planos_id"), table_name="planos_pagamentos")
    op.drop_table("planos_pagamentos")