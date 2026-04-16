from datetime import datetime
from uuid import UUID

from sqlalchemy import Index
from sqlalchemy.orm import Mapped

from app.database import BaseDbModel
from app.mappings import FKUser, PrimaryKey, str_10, str_100, str_255


class EatingEvent(BaseDbModel):
    """A single eating occurrence — one meal, snack, or drink.

    Timestamps are the input; eating/fasting windows are derived downstream
    by the insights service (consecutive events in the user's local timezone).
    """

    __tablename__ = "eating_event"
    __table_args__ = (Index("idx_eating_event_user_time", "user_id", "occurred_at"),)

    id: Mapped[PrimaryKey[UUID]]
    user_id: Mapped[FKUser]
    occurred_at: Mapped[datetime]
    zone_offset: Mapped[str_10 | None]
    label: Mapped[str_100 | None]
    notes: Mapped[str_255 | None]
    created_at: Mapped[datetime]
