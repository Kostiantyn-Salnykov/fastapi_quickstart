"""initial

Revision ID: 0001
Revises:
Create Date: 2022-09-27 19:29:54.643748+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sqltext="""CREATE EXTENSION IF NOT EXISTS pgcrypto""")


def downgrade() -> None:
    op.execute(sqltext="""DROP EXTENSION IF EXISTS pgcrypto""")
