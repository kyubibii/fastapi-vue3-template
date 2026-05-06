"""Add indexed is_deleted flag for soft-deleted audit tables.

Revision ID: 20260506_02
Revises: 20260506_01
Create Date: 2026-05-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260506_02"
down_revision = "20260506_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name in ("item", "user"):
        op.add_column(
            table_name,
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.execute(
            f"UPDATE {table_name} SET is_deleted = TRUE WHERE deleted_at IS NOT NULL"
        )
        op.create_index(
            f"ix_{table_name}_is_deleted",
            table_name,
            ["is_deleted"],
            unique=False,
        )

    for table_name in ("item", "user"):
        op.alter_column(table_name, "is_deleted", server_default=None)


def downgrade() -> None:
    for table_name in ("item", "user"):
        op.drop_index(f"ix_{table_name}_is_deleted", table_name=table_name)
        op.drop_column(table_name, "is_deleted")
