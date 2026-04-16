"""user_provider_priority

Revision ID: 827044c6368a
Revises: f99ae82f0470

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "827044c6368a"
down_revision: Union[str, None] = "f99ae82f0470"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_provider_priority",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider_priority"),
    )
    op.create_index(
        "idx_user_provider_priority_order",
        "user_provider_priority",
        ["user_id", "priority"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_user_provider_priority_order", table_name="user_provider_priority")
    op.drop_table("user_provider_priority")
