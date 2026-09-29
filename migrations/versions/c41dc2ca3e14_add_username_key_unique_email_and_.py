"""Add username key, unique email and indexes

Revision ID: c41dc2ca3e14
Revises: a5700d726eb5
Create Date: 2026-09-29 21:25:31.015833

"""

import unicodedata
from collections import Counter
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "c41dc2ca3e14"
down_revision: str | Sequence[str] | None = "a5700d726eb5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOT_EMPTY_EMAIL = sa.text("email != ''")

PRIMARY_KEY_TABLES = (
    "auth_user",
    "blog_category",
    "blog_location",
    "blog_post",
    "blog_comment",
)

LOOKUP_INDEXES = (
    ("blog_post", "author_id"),
    ("blog_post", "category_id"),
    ("blog_post", "location_id"),
    ("blog_post", "pub_date"),
    ("blog_comment", "author_id"),
    ("blog_comment", "post_id"),
)

users = sa.table(
    "auth_user",
    sa.column("id", sa.Integer),
    sa.column("username", sa.String),
    sa.column("username_key", sa.String),
    sa.column("email", sa.String),
)


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table(
        "auth_user", table_kwargs={"sqlite_autoincrement": True}
    ) as batch_op:
        batch_op.add_column(sa.Column("username_key", sa.String(), nullable=True))

    _normalize_users()

    with op.batch_alter_table(
        "auth_user", table_kwargs={"sqlite_autoincrement": True}
    ) as batch_op:
        batch_op.alter_column("username_key", existing_type=sa.String(), nullable=False)

    op.create_index(
        "uq_auth_user_username_key", "auth_user", ["username_key"], unique=True
    )
    op.create_index(
        "uq_auth_user_email",
        "auth_user",
        ["email"],
        unique=True,
        sqlite_where=NOT_EMPTY_EMAIL,
        postgresql_where=NOT_EMPTY_EMAIL,
    )
    for table in PRIMARY_KEY_TABLES:
        op.drop_index(f"ix_{table}_id", table_name=table)
    for table, column in LOOKUP_INDEXES:
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    """Downgrade schema."""
    for table, column in LOOKUP_INDEXES:
        op.drop_index(f"ix_{table}_{column}", table_name=table)
    for table in PRIMARY_KEY_TABLES:
        op.create_index(f"ix_{table}_id", table, ["id"])
    op.drop_index(
        "uq_auth_user_email",
        table_name="auth_user",
        sqlite_where=NOT_EMPTY_EMAIL,
        postgresql_where=NOT_EMPTY_EMAIL,
    )
    op.drop_index("uq_auth_user_username_key", table_name="auth_user")

    with op.batch_alter_table(
        "auth_user", table_kwargs={"sqlite_autoincrement": True}
    ) as batch_op:
        batch_op.drop_column("username_key")


def _normalize_users() -> None:
    if context.is_offline_mode():
        op.execute(
            "UPDATE auth_user SET username_key = lower(username), email = lower(email)"
        )
        return

    connection = op.get_bind()
    rows = connection.execute(
        sa.select(users.c.id, users.c.username, users.c.email)
    ).all()
    normalized = []
    for user_id, username, email in rows:
        username = unicodedata.normalize("NFKC", username)
        email = (email or "").strip().lower()
        normalized.append((user_id, username, username.casefold(), email))

    _ensure_unique("имена пользователей", [key for _, _, key, _ in normalized])
    _ensure_unique("email", [email for *_, email in normalized if email])

    for user_id, username, username_key, email in normalized:
        connection.execute(
            users.update()
            .where(users.c.id == user_id)
            .values(username=username, username_key=username_key, email=email)
        )


def _ensure_unique(field: str, values: list[str]) -> None:
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if duplicates:
        raise RuntimeError(
            f"Найдены повторяющиеся без учета регистра {field}: "
            f"{', '.join(duplicates)}. Исправьте данные и повторите миграцию."
        )
