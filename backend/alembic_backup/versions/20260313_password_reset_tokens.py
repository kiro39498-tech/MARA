"""add password reset token storage

Revision ID: 20260313_password_reset_tokens
Revises: 20260307_stock_adjustments
Create Date: 2026-03-13 10:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260313_password_reset_tokens"
down_revision = "20260307_stock_adjustments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                expires_at TIMESTAMPTZ NOT NULL,
                used_at TIMESTAMPTZ NULL,
                requested_ip VARCHAR(45) NULL,
                requested_user_agent VARCHAR(500) NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )

    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens (user_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_token_hash ON password_reset_tokens (token_hash)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_expires_at ON password_reset_tokens (expires_at)"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS password_reset_tokens"))
