"""Add refresh tokens

Revision ID: 28a63fa3f4b5
Revises: c41dc2ca3e14
Create Date: 2026-09-30 07:47:28.540303

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "28a63fa3f4b5"
down_revision: str | Sequence[str] | None = "c41dc2ca3e14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "auth_refresh_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth_user.id"],
            name="fk_auth_refresh_token_user_id_auth_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auth_refresh_token_family_id", "auth_refresh_token", ["family_id"]
    )
    op.create_index("ix_auth_refresh_token_user_id", "auth_refresh_token", ["user_id"])
    op.create_index(
        "uq_auth_refresh_token_token_hash",
        "auth_refresh_token",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_auth_refresh_token_token_hash", table_name="auth_refresh_token")
    op.drop_index("ix_auth_refresh_token_user_id", table_name="auth_refresh_token")
    op.drop_index("ix_auth_refresh_token_family_id", table_name="auth_refresh_token")
    op.drop_table("auth_refresh_token")
