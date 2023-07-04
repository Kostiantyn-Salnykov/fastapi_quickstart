"""initial.

Revision ID: 0001
Revises:
Create Date: 2022-09-27 19:29:54.643748+00:00

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;").execution_options(dialect_name="postgresql"))


def downgrade() -> None:
    op.execute(text("DROP EXTENSION IF EXISTS pgcrypto;").execution_options(dialect_name="postgresql"))
