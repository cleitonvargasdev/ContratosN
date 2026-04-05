"""rename bairro table to bairros

Revision ID: 20260404_0005
Revises: 20260404_0004
Create Date: 2026-04-04 00:30:00

"""

from alembic import op


revision = "20260404_0005"
down_revision = "20260404_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("bairro", "bairros")
    op.execute("ALTER INDEX ix_bairro_bairro_nome RENAME TO ix_bairros_bairro_nome")
    op.execute("ALTER INDEX ix_bairro_cidade_id RENAME TO ix_bairros_cidade_id")
    op.execute("ALTER TABLE bairros RENAME CONSTRAINT pk_bairro TO pk_bairros")
    op.execute("ALTER TABLE bairros RENAME CONSTRAINT fk_bairro_cidade_id TO fk_bairros_cidade_id")
    op.execute(
        "ALTER TABLE bairros RENAME CONSTRAINT uq_bairro_cidade_id_bairro_nome TO uq_bairros_cidade_id_bairro_nome"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE bairros RENAME CONSTRAINT uq_bairros_cidade_id_bairro_nome TO uq_bairro_cidade_id_bairro_nome"
    )
    op.execute("ALTER TABLE bairros RENAME CONSTRAINT fk_bairros_cidade_id TO fk_bairro_cidade_id")
    op.execute("ALTER TABLE bairros RENAME CONSTRAINT pk_bairros TO pk_bairro")
    op.execute("ALTER INDEX ix_bairros_cidade_id RENAME TO ix_bairro_cidade_id")
    op.execute("ALTER INDEX ix_bairros_bairro_nome RENAME TO ix_bairro_bairro_nome")
    op.rename_table("bairros", "bairro")