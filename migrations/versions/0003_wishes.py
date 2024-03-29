"""wishes.

Revision ID: 0003
Revises: 0002
Create Date: 2023-01-06 21:37:27.033878+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tag",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("title", sa.VARCHAR(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tag")),
    )
    op.create_index(op.f("ix_tag_title"), "tag", ["title"], unique=False)
    op.create_table(
        "category",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("title", sa.VARCHAR(length=128), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.id"],
            name=op.f("fk_category_owner_id_user"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_category")),
    )
    op.create_index(op.f("ix_category_title"), "category", ["title"], unique=False)
    op.create_table(
        "wish_list",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("title", sa.VARCHAR(length=128), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.id"],
            name=op.f("fk_wish_list_owner_id_user"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wish_list")),
    )
    op.create_index(op.f("ix_wish_list_title"), "wish_list", ["title"], unique=False)
    op.create_table(
        "wish",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("wishlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.VARCHAR(length=128), nullable=False),
        sa.Column("description", sa.VARCHAR(length=255), nullable=True),
        sa.Column("status", sa.VARCHAR(length=32), nullable=False),
        sa.Column("complexity", sa.VARCHAR(length=32), nullable=False),
        sa.Column("priority", sa.SMALLINT(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["category.id"],
            name=op.f("fk_wish_category_id_category"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["wishlist_id"],
            ["wish_list.id"],
            name=op.f("fk_wish_wishlist_id_wish_list"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wish")),
    )
    op.create_index(op.f("ix_wish_title"), "wish", ["title"], unique=False)
    op.create_table(
        "wish_tag",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("wish_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tag.id"],
            name=op.f("fk_wish_tag_tag_id_tag"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["wish_id"],
            ["wish.id"],
            name=op.f("fk_wish_tag_wish_id_wish"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("wish_id", "tag_id", name=op.f("pk_wish_tag")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("wish_tag")
    op.drop_index(op.f("ix_wish_title"), table_name="wish")
    op.drop_table("wish")
    op.drop_index(op.f("ix_wish_list_title"), table_name="wish_list")
    op.drop_table("wish_list")
    op.drop_index(op.f("ix_category_title"), table_name="category")
    op.drop_table("category")
    op.drop_index(op.f("ix_tag_title"), table_name="tag")
    op.drop_table("tag")
    # ### end Alembic commands ###
