"""Add foreign key actions and not null constraints

Revision ID: a5700d726eb5
Revises: 8f41f800dc74
Create Date: 2026-09-29 20:33:39.713770

"""

import logging
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from alembic.operations import BatchOperations

# revision identifiers, used by Alembic.
revision: str = "a5700d726eb5"
down_revision: str | Sequence[str] | None = "8f41f800dc74"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger("alembic.runtime.migration")

NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

CLEANUP_STATEMENTS = (
    (
        "DELETE FROM blog_post WHERE author_id NOT IN (SELECT id FROM auth_user)",
        "Удалено публикаций несуществующих авторов: %s",
    ),
    (
        "UPDATE blog_post SET category_id = NULL WHERE category_id IS NOT NULL "
        "AND category_id NOT IN (SELECT id FROM blog_category)",
        "Сброшена ссылка на несуществующую категорию у публикаций: %s",
    ),
    (
        "UPDATE blog_post SET location_id = NULL WHERE location_id IS NOT NULL "
        "AND location_id NOT IN (SELECT id FROM blog_location)",
        "Сброшена ссылка на несуществующее местоположение у публикаций: %s",
    ),
    (
        "DELETE FROM blog_comment "
        "WHERE post_id NOT IN (SELECT id FROM blog_post) "
        "OR author_id NOT IN (SELECT id FROM auth_user)",
        "Удалено комментариев к несуществующим публикациям или авторам: %s",
    ),
)

NULL_DEFAULTS = (
    ("auth_user", "is_active", "TRUE"),
    ("auth_user", "is_superuser", "FALSE"),
    ("auth_user", "date_joined", "CURRENT_TIMESTAMP"),
    ("blog_category", "is_published", "TRUE"),
    ("blog_category", "created_at", "CURRENT_TIMESTAMP"),
    ("blog_location", "is_published", "TRUE"),
    ("blog_location", "created_at", "CURRENT_TIMESTAMP"),
    ("blog_post", "is_published", "TRUE"),
    ("blog_post", "created_at", "CURRENT_TIMESTAMP"),
    ("blog_comment", "created_at", "CURRENT_TIMESTAMP"),
)

POST_FOREIGN_KEYS = (
    ("author_id", "auth_user", "CASCADE"),
    ("category_id", "blog_category", "SET NULL"),
    ("location_id", "blog_location", "SET NULL"),
)

COMMENT_FOREIGN_KEYS = (
    ("author_id", "auth_user", "CASCADE"),
    ("post_id", "blog_post", "CASCADE"),
)


def upgrade() -> None:
    """Upgrade schema."""
    for statement, message in CLEANUP_STATEMENTS:
        _execute_cleanup(statement, message)
    for table, column, default in NULL_DEFAULTS:
        op.execute(f"UPDATE {table} SET {column} = {default} WHERE {column} IS NULL")

    with op.batch_alter_table(
        "auth_user", table_kwargs={"sqlite_autoincrement": True}
    ) as batch_op:
        batch_op.alter_column("is_active", existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column(
            "is_superuser", existing_type=sa.Boolean(), nullable=False
        )
        batch_op.alter_column(
            "date_joined", existing_type=sa.DateTime(), nullable=False
        )

    with op.batch_alter_table("blog_category") as batch_op:
        batch_op.alter_column(
            "is_published", existing_type=sa.Boolean(), nullable=False
        )
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)

    with op.batch_alter_table("blog_location") as batch_op:
        batch_op.alter_column(
            "is_published", existing_type=sa.Boolean(), nullable=False
        )
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)

    post_foreign_keys = _foreign_key_names("blog_post", POST_FOREIGN_KEYS)
    with op.batch_alter_table(
        "blog_post", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.alter_column(
            "is_published", existing_type=sa.Boolean(), nullable=False
        )
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)
        _recreate_foreign_keys(
            batch_op, "blog_post", POST_FOREIGN_KEYS, post_foreign_keys, True
        )

    comment_foreign_keys = _foreign_key_names("blog_comment", COMMENT_FOREIGN_KEYS)
    with op.batch_alter_table(
        "blog_comment", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)
        _recreate_foreign_keys(
            batch_op, "blog_comment", COMMENT_FOREIGN_KEYS, comment_foreign_keys, True
        )


def downgrade() -> None:
    """Downgrade schema."""
    comment_foreign_keys = _foreign_key_names("blog_comment", COMMENT_FOREIGN_KEYS)
    with op.batch_alter_table(
        "blog_comment", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        _recreate_foreign_keys(
            batch_op, "blog_comment", COMMENT_FOREIGN_KEYS, comment_foreign_keys, False
        )
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)

    post_foreign_keys = _foreign_key_names("blog_post", POST_FOREIGN_KEYS)
    with op.batch_alter_table(
        "blog_post", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        _recreate_foreign_keys(
            batch_op, "blog_post", POST_FOREIGN_KEYS, post_foreign_keys, False
        )
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)
        batch_op.alter_column("is_published", existing_type=sa.Boolean(), nullable=True)

    with op.batch_alter_table("blog_location") as batch_op:
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)
        batch_op.alter_column("is_published", existing_type=sa.Boolean(), nullable=True)

    with op.batch_alter_table("blog_category") as batch_op:
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)
        batch_op.alter_column("is_published", existing_type=sa.Boolean(), nullable=True)

    with op.batch_alter_table(
        "auth_user", table_kwargs={"sqlite_autoincrement": False}
    ) as batch_op:
        batch_op.alter_column("date_joined", existing_type=sa.DateTime(), nullable=True)
        batch_op.alter_column("is_superuser", existing_type=sa.Boolean(), nullable=True)
        batch_op.alter_column("is_active", existing_type=sa.Boolean(), nullable=True)


def _execute_cleanup(statement: str, message: str) -> None:
    if context.is_offline_mode():
        op.execute(statement)
        return
    affected = op.get_bind().execute(sa.text(statement)).rowcount
    if affected:
        logger.warning(message, affected)


def _convention_name(table: str, column: str, referred_table: str) -> str:
    return NAMING_CONVENTION["fk"] % {
        "table_name": table,
        "column_0_name": column,
        "referred_table_name": referred_table,
    }


def _foreign_key_names(
    table: str, foreign_keys: Sequence[tuple[str, str, str]]
) -> list[str]:
    existing = (
        []
        if context.is_offline_mode()
        else sa.inspect(op.get_bind()).get_foreign_keys(table)
    )
    names = []
    for column, referred_table, _ in foreign_keys:
        name = next(
            (
                foreign_key["name"]
                for foreign_key in existing
                if foreign_key["constrained_columns"] == [column]
                and foreign_key["name"]
            ),
            _convention_name(table, column, referred_table),
        )
        names.append(name)
    return names


def _recreate_foreign_keys(
    batch_op: BatchOperations,
    table: str,
    foreign_keys: Sequence[tuple[str, str, str]],
    current_names: list[str],
    with_actions: bool,
) -> None:
    for name in current_names:
        batch_op.drop_constraint(name, type_="foreignkey")
    for column, referred_table, ondelete in foreign_keys:
        batch_op.create_foreign_key(
            _convention_name(table, column, referred_table),
            referred_table,
            [column],
            ["id"],
            ondelete=ondelete if with_actions else None,
        )
