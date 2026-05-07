"""Add user gender enum field.

Revision ID: 20260507_02
Revises: 20260507_01
Create Date: 2026-05-07
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260507_02"
down_revision = "20260507_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "gender",
            sa.Enum("male", "female", "other", "undisclosed", name="genderenum"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("user", "gender")
    op.execute("DROP TYPE IF EXISTS genderenum")
