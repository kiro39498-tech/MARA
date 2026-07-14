"""warehouse management fields and permissions

Revision ID: 20260307_warehouse_management
Revises:
Create Date: 2026-03-07 12:10:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260307_warehouse_management"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing warehouse field.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            ALTER TABLE warehouses
            ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255)
            """
        )
    )

    # Add search/filter indexes.
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_warehouses_name ON warehouses (name)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_warehouses_city ON warehouses (city)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_warehouses_is_active ON warehouses (is_active)"))

    # Add warehouse permissions if they do not exist.
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (name, description, resource, action)
            SELECT :name, :description, :resource, :action
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE name = :name
            )
            """
        ),
        {"name": "warehouse:view", "description": "View warehouses", "resource": "warehouse", "action": "view"},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (name, description, resource, action)
            SELECT :name, :description, :resource, :action
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE name = :name
            )
            """
        ),
        {"name": "warehouse:create", "description": "Create warehouses", "resource": "warehouse", "action": "create"},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (name, description, resource, action)
            SELECT :name, :description, :resource, :action
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE name = :name
            )
            """
        ),
        {"name": "warehouse:update", "description": "Update warehouses", "resource": "warehouse", "action": "update"},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (name, description, resource, action)
            SELECT :name, :description, :resource, :action
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE name = :name
            )
            """
        ),
        {"name": "warehouse:delete", "description": "Delete warehouses", "resource": "warehouse", "action": "delete"},
    )

    # Map permissions to standard roles if roles exist.
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            JOIN permissions p ON p.name IN ('warehouse:view', 'warehouse:create', 'warehouse:update', 'warehouse:delete')
            WHERE UPPER(r.name) IN ('ADMIN', 'HR', 'MANAGER')
            ON CONFLICT DO NOTHING
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            JOIN permissions p ON p.name = 'warehouse:view'
            WHERE UPPER(r.name) IN ('STAFF')
            ON CONFLICT DO NOTHING
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Remove permission mappings and permissions.
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions
                WHERE name IN ('warehouse:view', 'warehouse:create', 'warehouse:update', 'warehouse:delete')
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE name IN ('warehouse:view', 'warehouse:create', 'warehouse:update', 'warehouse:delete')
            """
        )
    )

    conn.execute(sa.text("DROP INDEX IF EXISTS ix_warehouses_is_active"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_warehouses_city"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_warehouses_name"))
    conn.execute(sa.text("ALTER TABLE warehouses DROP COLUMN IF EXISTS contact_person"))
