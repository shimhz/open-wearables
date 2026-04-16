from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import BaseDbModel
from app.mappings import FKUser, PrimaryKey, numeric_10_3, str_10


class HabitLog(BaseDbModel):
    """One habit value per user per local day.

    `logged_for_date` is the day this entry counts toward in the user's
    local timezone — set by the caller, not inferred from `logged_at`.
    """

    __tablename__ = "habit_log"
    __table_args__ = (UniqueConstraint("habit_definition_id", "logged_for_date", name="uq_habit_log_definition_date"),)

    id: Mapped[PrimaryKey[UUID]]
    user_id: Mapped[FKUser]
    habit_definition_id: Mapped[UUID] = mapped_column(ForeignKey("habit_definition.id", ondelete="CASCADE"))
    logged_for_date: Mapped[date]
    value: Mapped[numeric_10_3]
    logged_at: Mapped[datetime]
    zone_offset: Mapped[str_10 | None]
