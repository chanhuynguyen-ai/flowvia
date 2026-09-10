"""Align identity uniqueness metadata with the PostgreSQL schema.

Revision ID: 20260910_0004
Revises: 20260910_0003

The M1 migration created both a UNIQUE constraint and a unique index for
users.email and auth_sessions.token_hash. The ORM models represent those
fields as unique indexes (unique=True + index=True), so Alembic correctly
reports the extra PostgreSQL UNIQUE constraints as schema drift.

Keep the unique indexes, remove only the redundant constraints.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260910_0004"
down_revision: Union[str, Sequence[str], None] = "20260910_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "users_email_key",
        "users",
        type_="unique",
    )
    op.drop_constraint(
        "auth_sessions_token_hash_key",
        "auth_sessions",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "users_email_key",
        "users",
        ["email"],
    )
    op.create_unique_constraint(
        "auth_sessions_token_hash_key",
        "auth_sessions",
        ["token_hash"],
    )