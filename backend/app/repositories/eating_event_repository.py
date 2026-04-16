from datetime import datetime
from uuid import UUID

from sqlalchemy import asc, desc

from app.database import DbSession
from app.models import EatingEvent


class EatingEventRepository:
    def __init__(self, model: type[EatingEvent] = EatingEvent):
        self.model = model

    def get_by_id(self, db_session: DbSession, user_id: UUID, event_id: UUID) -> EatingEvent | None:
        return (
            db_session.query(self.model).filter(self.model.user_id == user_id, self.model.id == event_id).one_or_none()
        )

    def list_for_user(
        self,
        db_session: DbSession,
        user_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
        order: str = "asc",
    ) -> list[EatingEvent]:
        q = db_session.query(self.model).filter(self.model.user_id == user_id)
        if start is not None:
            q = q.filter(self.model.occurred_at >= start)
        if end is not None:
            q = q.filter(self.model.occurred_at < end)
        sort = asc if order == "asc" else desc
        return q.order_by(sort(self.model.occurred_at)).all()

    def create(self, db_session: DbSession, event: EatingEvent) -> EatingEvent:
        db_session.add(event)
        db_session.flush()
        return event

    def delete(self, db_session: DbSession, user_id: UUID, event_id: UUID) -> bool:
        deleted = (
            db_session.query(self.model)
            .filter(self.model.user_id == user_id, self.model.id == event_id)
            .delete(synchronize_session=False)
        )
        db_session.flush()
        return deleted > 0
