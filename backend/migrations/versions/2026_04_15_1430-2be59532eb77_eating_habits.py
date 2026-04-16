"""eating events and habits

Revision ID: 2be59532eb77
Revises: cdac07b15b04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2be59532eb77"
down_revision: Union[str, None] = "cdac07b15b04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eating_event",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zone_offset", sa.String(length=10), nullable=True),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_eating_event_user_time",
        "eating_event",
        ["user_id", "occurred_at"],
        unique=False,
    )

    op.create_table(
        "habit_definition",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_habit_definition_user_name"),
    )

    op.create_table(
        "habit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("habit_definition_id", sa.UUID(), nullable=False),
        sa.Column("logged_for_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(10, 3), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zone_offset", sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["habit_definition_id"], ["habit_definition.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("habit_definition_id", "logged_for_date", name="uq_habit_log_definition_date"),
    )
    op.create_index(
        "idx_habit_log_user_date",
        "habit_log",
        ["user_id", "logged_for_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_habit_log_user_date", table_name="habit_log")
    op.drop_table("habit_log")
    op.drop_table("habit_definition")
    op.drop_index("idx_eating_event_user_time", table_name="eating_event")
    op.drop_table("eating_event")
