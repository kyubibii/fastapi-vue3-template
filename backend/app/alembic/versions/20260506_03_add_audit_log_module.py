"""Add module field for audit log filtering.

Revision ID: 20260506_03
Revises: 20260506_02
Create Date: 2026-05-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260506_03"
down_revision = "20260506_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("module", sa.String(length=100), nullable=True))
    op.create_index("ix_audit_log_module", "audit_log", ["module"], unique=False)
    op.execute(
        """
        UPDATE audit_log
        SET module = SUBSTRING_INDEX(SUBSTRING(endpoint, 9), '/', 1)
        WHERE endpoint LIKE '/api/v1/%'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_module", table_name="audit_log")
    op.drop_column("audit_log", "module")
