"""alter produtos values to numeric

Revision ID: 20260506_0042
Revises: 20260506_0041
Create Date: 2026-05-06 13:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_0042"
down_revision = "20260506_0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "produtos",
        "valor_compra",
        existing_type=sa.Float(),
        type_=sa.Numeric(19, 2, asdecimal=False),
        postgresql_using="round(valor_compra::numeric, 2)",
        existing_nullable=True,
    )
    op.alter_column(
        "produtos",
        "valor_venda",
        existing_type=sa.Float(),
        type_=sa.Numeric(19, 2, asdecimal=False),
        postgresql_using="round(valor_venda::numeric, 2)",
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "produtos",
        "valor_venda",
        existing_type=sa.Numeric(19, 2, asdecimal=False),
        type_=sa.Float(),
        postgresql_using="valor_venda::double precision",
        existing_nullable=True,
    )
    op.alter_column(
        "produtos",
        "valor_compra",
        existing_type=sa.Numeric(19, 2, asdecimal=False),
        type_=sa.Float(),
        postgresql_using="valor_compra::double precision",
        existing_nullable=True,
    )