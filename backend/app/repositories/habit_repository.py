from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import asc
from sqlalchemy.dialects.postgresql import insert

from app.database import DbSession
from app.models import HabitDefinition, HabitLog


class HabitDefinitionRepository:
    def __init__(self, model: type[HabitDefinition] = HabitDefinition):
        self.model = model

    def get_by_id(self, db_session: DbSession, user_id: UUID, habit_id: UUID) -> HabitDefinition | None:
        return (
            db_session.query(self.model).filter(self.model.user_id == user_id, self.model.id == habit_id).one_or_none()
        )

    def list_for_user(
        self,
        db_session: DbSession,
        user_id: UUID,
        include_archived: bool = False,
    ) -> list[HabitDefinition]:
        q = db_session.query(self.model).filter(self.model.user_id == user_id)
        if not include_archived:
            q = q.filter(self.model.archived.is_(False))
        return q.order_by(asc(self.model.name)).all()

    def get_by_name(self, db_session: DbSession, user_id: UUID, name: str) -> HabitDefinition | None:
        return db_session.query(self.model).filter(self.model.user_id == user_id, self.model.name == name).one_or_none()

    def create(self, db_session: DbSession, habit: HabitDefinition) -> HabitDefinition:
        db_session.add(habit)
        db_session.flush()
        return habit


class HabitLogRepository:
    def __init__(self, model: type[HabitLog] = HabitLog):
        self.model = model

    def list_for_user(
        self,
        db_session: DbSession,
        user_id: UUID,
        habit_definition_id: UUID | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[HabitLog]:
        q = db_session.query(self.model).filter(self.model.user_id == user_id)
        if habit_definition_id is not None:
            q = q.filter(self.model.habit_definition_id == habit_definition_id)
        if start is not None:
            q = q.filter(self.model.logged_for_date >= start)
        if end is not None:
            q = q.filter(self.model.logged_for_date <= end)
        return q.order_by(asc(self.model.logged_for_date)).all()

    def upsert(
        self,
        db_session: DbSession,
        user_id: UUID,
        habit_definition_id: UUID,
        logged_for_date: date,
        value: Decimal,
        zone_offset: str | None,
    ) -> HabitLog:
        now = datetime.now(timezone.utc)
        stmt = (
            insert(self.model)
            .values(
                id=uuid4(),
                user_id=user_id,
                habit_definition_id=habit_definition_id,
                logged_for_date=logged_for_date,
                value=value,
                logged_at=now,
                zone_offset=zone_offset,
            )
            .on_conflict_do_update(
                constraint="uq_habit_log_definition_date",
                set_={"value": value, "logged_at": now, "zone_offset": zone_offset},
            )
        )
        db_session.execute(stmt)
        db_session.flush()
        return (
            db_session.query(self.model)
            .filter(
                self.model.habit_definition_id == habit_definition_id,
                self.model.logged_for_date == logged_for_date,
            )
            .one()
        )
