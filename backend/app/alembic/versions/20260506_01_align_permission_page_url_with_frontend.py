"""Align permission_page.page_url with frontend route paths.

Revision ID: 20260506_01
Revises:
Create Date: 2026-05-06
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260506_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE permission_page
        SET page_url = CASE page_url
            WHEN '/admin/items' THEN '/items'
            WHEN '/admin/users' THEN '/users'
            WHEN '/admin/audit-logs' THEN '/audit-logs'
            WHEN '/admin/roles' THEN '/roles'
            ELSE page_url
        END
        WHERE page_url IN ('/admin/items', '/admin/users', '/admin/audit-logs', '/admin/roles')
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE permission_page
        SET page_url = CASE page_url
            WHEN '/items' THEN '/admin/items'
            WHEN '/users' THEN '/admin/users'
            WHEN '/audit-logs' THEN '/admin/audit-logs'
            WHEN '/roles' THEN '/admin/roles'
            ELSE page_url
        END
        WHERE page_url IN ('/items', '/users', '/audit-logs', '/roles')
        """
    )
