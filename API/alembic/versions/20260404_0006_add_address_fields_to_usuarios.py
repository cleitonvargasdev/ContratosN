"""add address fields to usuarios

Revision ID: 20260404_0006
Revises: 20260404_0005
Create Date: 2026-04-04 01:00:00

"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0006"
down_revision = "20260404_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("cep", sa.String(length=8), nullable=True))
    op.add_column("usuarios", sa.Column("endereco", sa.String(length=255), nullable=True))
    op.add_column("usuarios", sa.Column("numero", sa.String(length=20), nullable=True))
    op.add_column("usuarios", sa.Column("complemento", sa.String(length=120), nullable=True))
    op.add_column("usuarios", sa.Column("bairro_id", sa.Integer(), nullable=True))
    op.add_column("usuarios", sa.Column("cidade_id", sa.BigInteger(), nullable=True))
    op.add_column("usuarios", sa.Column("uf", sa.String(length=2), nullable=True))
    op.add_column("usuarios", sa.Column("cpf", sa.String(length=11), nullable=True))
    op.add_column("usuarios", sa.Column("rg", sa.String(length=20), nullable=True))
    op.add_column("usuarios", sa.Column("celular", sa.String(length=20), nullable=True))
    op.add_column("usuarios", sa.Column("flag_whatsapp", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("usuarios", sa.Column("data_nascimento", sa.Date(), nullable=True))

    op.create_foreign_key("fk_usuarios_bairro_id", "usuarios", "bairros", ["bairro_id"], ["bairro_id"], ondelete="SET NULL")
    op.create_foreign_key("fk_usuarios_cidade_id", "usuarios", "cidades", ["cidade_id"], ["cidade_id"], ondelete="SET NULL")
    op.create_foreign_key("fk_usuarios_uf", "usuarios", "uf", ["uf"], ["uf"], ondelete="SET NULL")

    op.create_index("ix_usuarios_cep", "usuarios", ["cep"], unique=False)
    op.create_index("ix_usuarios_cpf", "usuarios", ["cpf"], unique=False)
    op.create_index("ix_usuarios_bairro_id", "usuarios", ["bairro_id"], unique=False)
    op.create_index("ix_usuarios_cidade_id", "usuarios", ["cidade_id"], unique=False)
    op.create_index("ix_usuarios_uf", "usuarios", ["uf"], unique=False)

    op.execute(
        """
        INSERT INTO bairros (bairro_nome, cidade_id)
        SELECT 'Centro', cidade_id FROM cidades WHERE cidade = 'Campo Grande'
        AND NOT EXISTS (
            SELECT 1 FROM bairros b
            WHERE b.cidade_id = cidades.cidade_id AND b.bairro_nome = 'Centro'
        )
        """
    )
    op.execute(
        """
        INSERT INTO bairros (bairro_nome, cidade_id)
        SELECT 'Jardim dos Estados', cidade_id FROM cidades WHERE cidade = 'Campo Grande'
        AND NOT EXISTS (
            SELECT 1 FROM bairros b
            WHERE b.cidade_id = cidades.cidade_id AND b.bairro_nome = 'Jardim dos Estados'
        )
        """
    )
    op.execute(
        """
        INSERT INTO bairros (bairro_nome, cidade_id)
        SELECT 'Centro Norte', cidade_id FROM cidades WHERE cidade = 'Cuiaba'
        AND NOT EXISTS (
            SELECT 1 FROM bairros b
            WHERE b.cidade_id = cidades.cidade_id AND b.bairro_nome = 'Centro Norte'
        )
        """
    )
    op.execute(
        """
        INSERT INTO bairros (bairro_nome, cidade_id)
        SELECT 'CPA I', cidade_id FROM cidades WHERE cidade = 'Cuiaba'
        AND NOT EXISTS (
            SELECT 1 FROM bairros b
            WHERE b.cidade_id = cidades.cidade_id AND b.bairro_nome = 'CPA I'
        )
        """
    )

    op.alter_column("usuarios", "flag_whatsapp", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_usuarios_uf", table_name="usuarios")
    op.drop_index("ix_usuarios_cidade_id", table_name="usuarios")
    op.drop_index("ix_usuarios_bairro_id", table_name="usuarios")
    op.drop_index("ix_usuarios_cpf", table_name="usuarios")
    op.drop_index("ix_usuarios_cep", table_name="usuarios")

    op.drop_constraint("fk_usuarios_uf", "usuarios", type_="foreignkey")
    op.drop_constraint("fk_usuarios_cidade_id", "usuarios", type_="foreignkey")
    op.drop_constraint("fk_usuarios_bairro_id", "usuarios", type_="foreignkey")

    op.drop_column("usuarios", "data_nascimento")
    op.drop_column("usuarios", "flag_whatsapp")
    op.drop_column("usuarios", "celular")
    op.drop_column("usuarios", "rg")
    op.drop_column("usuarios", "cpf")
    op.drop_column("usuarios", "uf")
    op.drop_column("usuarios", "cidade_id")
    op.drop_column("usuarios", "bairro_id")
    op.drop_column("usuarios", "complemento")
    op.drop_column("usuarios", "numero")
    op.drop_column("usuarios", "endereco")
    op.drop_column("usuarios", "cep")