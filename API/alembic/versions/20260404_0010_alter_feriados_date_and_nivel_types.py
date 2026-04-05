"""alter feriados date and nivel types

Revision ID: 20260404_0010
Revises: 20260404_0009
Create Date: 2026-04-04 21:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0010"
down_revision = "20260404_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "feriados",
        "data",
        existing_type=sa.String(length=10),
        type_=sa.Date(),
        postgresql_using=(
            "CASE "
            "WHEN data ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}$' THEN to_date(data, 'DD/MM/YYYY') "
            "WHEN data ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN to_date(data, 'YYYY-MM-DD') "
            "ELSE NULL END"
        ),
        existing_nullable=False,
    )
    op.alter_column(
        "feriados",
        "nivel",
        existing_type=sa.String(length=20),
        type_=sa.Numeric(precision=1, scale=0, asdecimal=False),
        postgresql_using=(
            "CASE upper(trim(nivel)) "
            "WHEN 'NACIONAL' THEN 1 "
            "WHEN 'ESTADUAL' THEN 2 "
            "WHEN 'MUNICIPAL' THEN 3 "
            "ELSE NULL END"
        ),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "feriados",
        "nivel",
        existing_type=sa.Numeric(precision=1, scale=0, asdecimal=False),
        type_=sa.String(length=20),
        postgresql_using=(
            "CASE nivel "
            "WHEN 1 THEN 'NACIONAL' "
            "WHEN 2 THEN 'ESTADUAL' "
            "WHEN 3 THEN 'MUNICIPAL' "
            "ELSE NULL END"
        ),
        existing_nullable=False,
    )
    op.alter_column(
        "feriados",
        "data",
        existing_type=sa.Date(),
        type_=sa.String(length=10),
        postgresql_using="to_char(data, 'YYYY-MM-DD')",
        existing_nullable=False,
    )
