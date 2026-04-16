from datetime import date, datetime, timezone
from logging import Logger, getLogger
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import DbSession
from app.models import HabitDefinition
from app.repositories import HabitDefinitionRepository, HabitLogRepository
from app.schemas.model_crud.habit import (
    HabitDefinitionCreate,
    HabitDefinitionListResponse,
    HabitDefinitionResponse,
    HabitDefinitionUpdate,
    HabitLogListResponse,
    HabitLogResponse,
    HabitLogUpsert,
)
from app.utils.exceptions import handle_exceptions


class HabitService:
    def __init__(self, log: Logger):
        self.logger = log
        self.definition_repo = HabitDefinitionRepository()
        self.log_repo = HabitLogRepository()

    @handle_exceptions
    def list_definitions(
        self,
        db_session: DbSession,
        user_id: UUID,
        include_archived: bool,
    ) -> HabitDefinitionListResponse:
        habits = self.definition_repo.list_for_user(db_session, user_id, include_archived)
        return HabitDefinitionListResponse(items=[HabitDefinitionResponse.model_validate(h) for h in habits])

    @handle_exceptions
    def create_definition(
        self,
        db_session: DbSession,
        user_id: UUID,
        payload: HabitDefinitionCreate,
    ) -> HabitDefinitionResponse:
        if self.definition_repo.get_by_name(db_session, user_id, payload.name) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Habit '{payload.name}' already exists",
            )
        now = datetime.now(timezone.utc)
        habit = HabitDefinition(
            id=uuid4(),
            user_id=user_id,
            name=payload.name,
            kind=payload.kind,
            unit=payload.unit,
            archived=False,
            created_at=now,
            updated_at=now,
        )
        self.definition_repo.create(db_session, habit)
        db_session.commit()
        return HabitDefinitionResponse.model_validate(habit)

    @handle_exceptions
    def update_definition(
        self,
        db_session: DbSession,
        user_id: UUID,
        habit_id: UUID,
        payload: HabitDefinitionUpdate,
    ) -> HabitDefinitionResponse:
        habit = self.definition_repo.get_by_id(db_session, user_id, habit_id)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(habit, field, value)
        habit.updated_at = datetime.now(timezone.utc)
        db_session.flush()
        db_session.commit()
        return HabitDefinitionResponse.model_validate(habit)

    @handle_exceptions
    def list_logs(
        self,
        db_session: DbSession,
        user_id: UUID,
        habit_id: UUID | None,
        start: date | None,
        end: date | None,
    ) -> HabitLogListResponse:
        logs = self.log_repo.list_for_user(db_session, user_id, habit_id, start, end)
        return HabitLogListResponse(items=[HabitLogResponse.model_validate(log) for log in logs])

    @handle_exceptions
    def upsert_log(
        self,
        db_session: DbSession,
        user_id: UUID,
        payload: HabitLogUpsert,
    ) -> HabitLogResponse:
        habit = self.definition_repo.get_by_id(db_session, user_id, payload.habit_definition_id)
        if habit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Habit not found for this user",
            )
        log = self.log_repo.upsert(
            db_session,
            user_id=user_id,
            habit_definition_id=payload.habit_definition_id,
            logged_for_date=payload.logged_for_date,
            value=payload.value,
            zone_offset=payload.zone_offset,
        )
        db_session.commit()
        return HabitLogResponse.model_validate(log)


habit_service = HabitService(log=getLogger(__name__))
