"""Allow the encrypted WhatsApp token to exceed the plaintext input length."""
from alembic import op
import sqlalchemy as sa

revision = "20261015_0050"
down_revision = "20260810_0049"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("parametros", "token_api_whatsapp", existing_type=sa.String(120), type_=sa.Text(), existing_nullable=True)


def downgrade():
    # PostgreSQL refuses values over 120 characters instead of truncating secrets.
    op.alter_column("parametros", "token_api_whatsapp", existing_type=sa.Text(), type_=sa.String(120), existing_nullable=True)
