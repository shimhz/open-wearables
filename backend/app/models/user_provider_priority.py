from datetime import datetime
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped

from app.database import BaseDbModel
from app.mappings import FKUser, Indexed, PrimaryKey
from app.schemas.enums import ProviderName


class UserProviderPriority(BaseDbModel):
    """Per-user override for provider priority.

    When present, takes precedence over the global `provider_priority` row
    for the same provider. Absent rows fall back to global defaults.
    """

    __tablename__ = "user_provider_priority"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider_priority"),)

    id: Mapped[PrimaryKey[UUID]]
    user_id: Mapped[FKUser]
    provider: Mapped[ProviderName]
    priority: Mapped[Indexed[int]]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
