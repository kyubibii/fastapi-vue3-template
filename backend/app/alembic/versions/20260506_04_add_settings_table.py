"""Add settings table for runtime configuration management.

Revision ID: 20260506_04
Revises: 20260506_03
Create Date: 2026-05-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260506_04"
down_revision = "20260506_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "setting",
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
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("setting_name", sa.String(length=100), nullable=False),
        sa.Column("setting_value", sa.String(length=4000), nullable=True),
        sa.Column("setting_group", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("value_type", sa.String(length=20), nullable=False),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_readonly", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_setting_is_deleted", "setting", ["is_deleted"], unique=False)
    op.create_index("ix_setting_setting_group", "setting", ["setting_group"], unique=False)
    op.create_index("ix_setting_setting_name", "setting", ["setting_name"], unique=True)
    op.alter_column("setting", "is_deleted", server_default=None)
    op.alter_column("setting", "is_sensitive", server_default=None)
    op.alter_column("setting", "is_encrypted", server_default=None)
    op.alter_column("setting", "is_readonly", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_setting_setting_name", table_name="setting")
    op.drop_index("ix_setting_setting_group", table_name="setting")
    op.drop_index("ix_setting_is_deleted", table_name="setting")
    op.drop_table("setting")