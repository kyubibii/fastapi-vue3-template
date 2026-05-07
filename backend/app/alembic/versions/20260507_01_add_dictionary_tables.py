"""Add dictionary type and item tables.

Revision ID: 20260507_01
Revises: 20260506_04
Create Date: 2026-05-07
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260507_01"
down_revision = "20260506_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dictionary_type",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type_code", sa.String(length=100), nullable=False),
        sa.Column("type_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dictionary_type_is_deleted",
        "dictionary_type",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        "ix_dictionary_type_sort_order",
        "dictionary_type",
        ["sort_order"],
        unique=False,
    )
    op.create_index(
        "ix_dictionary_type_type_code",
        "dictionary_type",
        ["type_code"],
        unique=True,
    )
    op.create_index(
        "ix_dictionary_type_type_name",
        "dictionary_type",
        ["type_name"],
        unique=False,
    )
    op.alter_column("dictionary_type", "is_deleted", server_default=None)

    op.create_table(
        "dictionary_item",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type_id", sa.Uuid(), nullable=False),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("item_label", sa.String(length=200), nullable=False),
        sa.Column("item_value", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["type_id"], ["dictionary_type.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type_id", "item_code", name="uq_dictionary_item_type_code"),
    )
    op.create_index(
        "ix_dictionary_item_enabled",
        "dictionary_item",
        ["enabled"],
        unique=False,
    )
    op.create_index(
        "ix_dictionary_item_is_deleted",
        "dictionary_item",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        "ix_dictionary_item_item_code",
        "dictionary_item",
        ["item_code"],
        unique=False,
    )
    op.create_index(
        "ix_dictionary_item_item_label",
        "dictionary_item",
        ["item_label"],
        unique=False,
    )
    op.create_index(
        "ix_dictionary_item_sort_order",
        "dictionary_item",
        ["sort_order"],
        unique=False,
    )
    op.create_index(
        "ix_dictionary_item_type_id",
        "dictionary_item",
        ["type_id"],
        unique=False,
    )
    op.alter_column("dictionary_item", "is_deleted", server_default=None)
    op.alter_column("dictionary_item", "enabled", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_dictionary_item_type_id", table_name="dictionary_item")
    op.drop_index("ix_dictionary_item_sort_order", table_name="dictionary_item")
    op.drop_index("ix_dictionary_item_item_label", table_name="dictionary_item")
    op.drop_index("ix_dictionary_item_item_code", table_name="dictionary_item")
    op.drop_index("ix_dictionary_item_is_deleted", table_name="dictionary_item")
    op.drop_index("ix_dictionary_item_enabled", table_name="dictionary_item")
    op.drop_table("dictionary_item")

    op.drop_index("ix_dictionary_type_type_name", table_name="dictionary_type")
    op.drop_index("ix_dictionary_type_type_code", table_name="dictionary_type")
    op.drop_index("ix_dictionary_type_sort_order", table_name="dictionary_type")
    op.drop_index("ix_dictionary_type_is_deleted", table_name="dictionary_type")
    op.drop_table("dictionary_type")
