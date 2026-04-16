from datetime import datetime, timezone
from logging import Logger, getLogger
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import DbSession
from app.models import EatingEvent
from app.repositories import EatingEventRepository
from app.schemas.model_crud.eating_event import (
    EatingEventCreate,
    EatingEventListResponse,
    EatingEventResponse,
    EatingEventUpdate,
)
from app.utils.exceptions import handle_exceptions


class EatingEventService:
    def __init__(self, log: Logger):
        self.logger = log
        self.repo = EatingEventRepository()

    @handle_exceptions
    def list_for_user(
        self,
        db_session: DbSession,
        user_id: UUID,
        start: datetime | None,
        end: datetime | None,
        order: str,
    ) -> EatingEventListResponse:
        events = self.repo.list_for_user(db_session, user_id, start, end, order)
        return EatingEventListResponse(items=[EatingEventResponse.model_validate(e) for e in events])

    @handle_exceptions
    def create(
        self,
        db_session: DbSession,
        user_id: UUID,
        payload: EatingEventCreate,
    ) -> EatingEventResponse:
        event = EatingEvent(
            id=uuid4(),
            user_id=user_id,
            occurred_at=payload.occurred_at,
            zone_offset=payload.zone_offset,
            label=payload.label,
            notes=payload.notes,
            created_at=datetime.now(timezone.utc),
        )
        self.repo.create(db_session, event)
        db_session.commit()
        return EatingEventResponse.model_validate(event)

    @handle_exceptions
    def update(
        self,
        db_session: DbSession,
        user_id: UUID,
        event_id: UUID,
        payload: EatingEventUpdate,
    ) -> EatingEventResponse:
        event = self.repo.get_by_id(db_session, user_id, event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eating event not found")
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(event, field, value)
        db_session.flush()
        db_session.commit()
        return EatingEventResponse.model_validate(event)

    @handle_exceptions
    def delete(self, db_session: DbSession, user_id: UUID, event_id: UUID) -> None:
        deleted = self.repo.delete(db_session, user_id, event_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eating event not found")
        db_session.commit()


eating_event_service = EatingEventService(log=getLogger(__name__))
