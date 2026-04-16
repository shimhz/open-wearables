from datetime import datetime
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped

from app.database import BaseDbModel
from app.mappings import FKUser, PrimaryKey, str_20, str_100
from app.schemas.enums.habit import HabitKind


class HabitDefinition(BaseDbModel):
    """A user-defined trackable habit.

    `kind` controls how `habit_log.value` is interpreted and how it rolls up
    across a week/month/year in the insights endpoint.
    """

    __tablename__ = "habit_definition"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_habit_definition_user_name"),)

    id: Mapped[PrimaryKey[UUID]]
    user_id: Mapped[FKUser]
    name: Mapped[str_100]
    kind: Mapped[HabitKind]
    unit: Mapped[str_20 | None]
    archived: Mapped[bool]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
