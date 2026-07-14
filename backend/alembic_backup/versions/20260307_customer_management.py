"""customer management and optional sales linkage

Revision ID: 20260307_customer_management
Revises: 20260307_warehouse_management
Create Date: 2026-03-07 13:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260307_customer_management"
down_revision = "20260307_warehouse_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                customer_code VARCHAR(50) NOT NULL UNIQUE,
                full_name VARCHAR(255) NOT NULL,
                company_name VARCHAR(255) NULL,
                email VARCHAR(255) NULL,
                phone VARCHAR(30) NULL,
                address TEXT NULL,
                city VARCHAR(100) NULL,
                customer_type VARCHAR(10) NOT NULL,
                credit_limit FLOAT NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                notes TEXT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT ck_customers_customer_type CHECK (customer_type IN ('individual','business')),
                CONSTRAINT ck_customers_credit_limit CHECK (credit_limit >= 0)
            )
            """
        )
    )

    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_customers_customer_code ON customers (customer_code)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_customers_full_name ON customers (full_name)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_customers_company_name ON customers (company_name)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_customers_phone ON customers (phone)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_customers_email ON customers (email)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_customers_city ON customers (city)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_customers_is_active ON customers (is_active)"))

    op.execute(sa.text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS customer_id INTEGER NULL"))
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'fk_sales_customer_id_customers'
                ) THEN
                    ALTER TABLE sales
                    ADD CONSTRAINT fk_sales_customer_id_customers
                    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE SET NULL;
                END IF;
            END $$;
            """
        )
    )
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_sales_customer_id ON sales (customer_id)"))

    conn = op.get_bind()
    permissions = [
        ("customer:view", "View customers", "customer", "view"),
        ("customer:create", "Create customers", "customer", "create"),
        ("customer:update", "Update customers", "customer", "update"),
        ("customer:delete", "Delete customers", "customer", "delete"),
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
            JOIN permissions p ON p.name IN ('customer:view', 'customer:create', 'customer:update', 'customer:delete')
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
            JOIN permissions p ON p.name = 'customer:view'
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
                WHERE name IN ('customer:view', 'customer:create', 'customer:update', 'customer:delete')
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE name IN ('customer:view', 'customer:create', 'customer:update', 'customer:delete')
            """
        )
    )

    op.execute(sa.text("DROP INDEX IF EXISTS ix_sales_customer_id"))
    op.execute(sa.text("ALTER TABLE sales DROP CONSTRAINT IF EXISTS fk_sales_customer_id_customers"))
    op.execute(sa.text("ALTER TABLE sales DROP COLUMN IF EXISTS customer_id"))

    op.execute(sa.text("DROP TABLE IF EXISTS customers"))
