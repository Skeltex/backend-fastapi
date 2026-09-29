"""Add foreign key actions and not null constraints

Revision ID: a5700d726eb5
Revises: 8f41f800dc74
Create Date: 2026-09-29 20:33:39.713770

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5700d726eb5"
down_revision: str | Sequence[str] | None = "8f41f800dc74"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

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


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE blog_post SET category_id = NULL "
        "WHERE category_id NOT IN (SELECT id FROM blog_category)"
    )
    op.execute(
        "UPDATE blog_post SET location_id = NULL "
        "WHERE location_id NOT IN (SELECT id FROM blog_location)"
    )
    op.execute(
        "DELETE FROM blog_post WHERE author_id NOT IN (SELECT id FROM auth_user)"
    )
    op.execute(
        "DELETE FROM blog_comment "
        "WHERE post_id NOT IN (SELECT id FROM blog_post) "
        "OR author_id NOT IN (SELECT id FROM auth_user)"
    )
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

    with op.batch_alter_table(
        "blog_post", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.alter_column(
            "is_published", existing_type=sa.Boolean(), nullable=False
        )
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.drop_constraint("fk_blog_post_author_id_auth_user", type_="foreignkey")
        batch_op.drop_constraint(
            "fk_blog_post_category_id_blog_category", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_blog_post_location_id_blog_location", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_blog_post_author_id_auth_user",
            "auth_user",
            ["author_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_blog_post_category_id_blog_category",
            "blog_category",
            ["category_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_blog_post_location_id_blog_location",
            "blog_location",
            ["location_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table(
        "blog_comment", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.drop_constraint(
            "fk_blog_comment_author_id_auth_user", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_blog_comment_post_id_blog_post", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_blog_comment_author_id_auth_user",
            "auth_user",
            ["author_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_blog_comment_post_id_blog_post",
            "blog_post",
            ["post_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table(
        "blog_comment", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_blog_comment_post_id_blog_post", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_blog_comment_author_id_auth_user", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_blog_comment_post_id_blog_post", "blog_post", ["post_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_blog_comment_author_id_auth_user", "auth_user", ["author_id"], ["id"]
        )
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=True)

    with op.batch_alter_table(
        "blog_post", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_blog_post_location_id_blog_location", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_blog_post_category_id_blog_category", type_="foreignkey"
        )
        batch_op.drop_constraint("fk_blog_post_author_id_auth_user", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_blog_post_location_id_blog_location",
            "blog_location",
            ["location_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_blog_post_category_id_blog_category",
            "blog_category",
            ["category_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_blog_post_author_id_auth_user", "auth_user", ["author_id"], ["id"]
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
