"""stock adjustments module

Revision ID: 20260307_stock_adjustments
Revises: 20260307_customer_management
Create Date: 2026-03-07 16:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260307_stock_adjustments"
down_revision = "20260307_customer_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS stock_adjustments (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id),
                warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
                adjustment_type VARCHAR(8) NOT NULL,
                quantity INTEGER NOT NULL,
                reason VARCHAR(255) NOT NULL,
                note TEXT NULL,
                adjustment_reference VARCHAR(100) NULL UNIQUE,
                created_by INTEGER NULL REFERENCES users(id),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT ck_stock_adjustments_adjustment_type
                    CHECK (adjustment_type IN ('INCREASE', 'DECREASE', 'increase', 'decrease')),
                CONSTRAINT ck_stock_adjustments_quantity CHECK (quantity > 0)
            )
            """
        )
    )

    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_stock_adjustments_product_id ON stock_adjustments (product_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_stock_adjustments_warehouse_id ON stock_adjustments (warehouse_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_stock_adjustments_created_at ON stock_adjustments (created_at)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_stock_adjustments_adjustment_reference ON stock_adjustments (adjustment_reference)"))

    conn = op.get_bind()
    permissions = [
        ("stock_adjustment:view", "View stock adjustments", "stock_adjustment", "view"),
        ("stock_adjustment:create", "Create stock adjustments", "stock_adjustment", "create"),
    ]
    for name, description, resource, action in permissions:
        conn.execute(
            sa.text(
                """
                INSERT INTO permissions (name, description, resource, action)
                SELECT :name, :description, :resource, :action
                WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE name = :name)
                """
            ),
            {
                "name": name,
                "description": description,
                "resource": resource,
                "action": action,
            },
        )

    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            JOIN permissions p ON p.name IN ('stock_adjustment:view', 'stock_adjustment:create')
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
            JOIN permissions p ON p.name = 'stock_adjustment:view'
            WHERE UPPER(r.name) = 'STAFF'
            ON CONFLICT DO NOTHING
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions
                WHERE name IN ('stock_adjustment:view', 'stock_adjustment:create')
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE name IN ('stock_adjustment:view', 'stock_adjustment:create')
            """
        )
    )

    op.execute(sa.text("DROP TABLE IF EXISTS stock_adjustments"))
