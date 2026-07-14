"""notifications inbox table

Revision ID: 20260313_notifications
Revises: 20260313_password_reset_tokens
Create Date: 2026-03-13 16:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260313_notifications"
down_revision = "20260313_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(20) NOT NULL DEFAULT 'info',
                action_url VARCHAR(255) NULL,
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                read_at TIMESTAMPTZ NULL,
                source_type VARCHAR(50) NOT NULL,
                source_id VARCHAR(100) NOT NULL,
                source_key VARCHAR(160) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_notifications_user_source_key UNIQUE (user_id, source_key)
            )
            """
        )
    )

    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications (is_read)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_notifications_source_type ON notifications (source_type)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_notifications_source_id ON notifications (source_id)"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS notifications"))
