"""Tests for HabitService."""

from datetime import date
from decimal import Decimal
from logging import getLogger

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.enums import HabitKind
from app.schemas.model_crud.habit import (
    HabitDefinitionCreate,
    HabitDefinitionUpdate,
    HabitLogUpsert,
)
from app.services.habit_service import HabitService
from tests.factories import UserFactory


@pytest.fixture
def service() -> HabitService:
    return HabitService(log=getLogger(__name__))


def test_create_and_list_excludes_archived_by_default(db: Session, service: HabitService) -> None:
    user = UserFactory()
    db.flush()

    h1 = service.create_definition(db, user.id, HabitDefinitionCreate(name="Meditate", kind=HabitKind.BOOLEAN))
    service.create_definition(db, user.id, HabitDefinitionCreate(name="Steps", kind=HabitKind.COUNT, unit="steps"))
    service.update_definition(db, user.id, h1.id, HabitDefinitionUpdate(archived=True))

    active = service.list_definitions(db, user.id, include_archived=False)
    assert {h.name for h in active.items} == {"Steps"}

    with_archived = service.list_definitions(db, user.id, include_archived=True)
    assert {h.name for h in with_archived.items} == {"Meditate", "Steps"}


def test_create_duplicate_name_409(db: Session, service: HabitService) -> None:
    user = UserFactory()
    db.flush()
    service.create_definition(db, user.id, HabitDefinitionCreate(name="Meditate", kind=HabitKind.BOOLEAN))

    with pytest.raises(HTTPException) as exc:
        service.create_definition(db, user.id, HabitDefinitionCreate(name="Meditate", kind=HabitKind.BOOLEAN))
    assert exc.value.status_code == 409


def test_upsert_log_overwrites_same_day(db: Session, service: HabitService) -> None:
    user = UserFactory()
    db.flush()
    habit = service.create_definition(db, user.id, HabitDefinitionCreate(name="Steps", kind=HabitKind.COUNT))
    d = date(2026, 4, 15)

    service.upsert_log(
        db, user.id, HabitLogUpsert(habit_definition_id=habit.id, logged_for_date=d, value=Decimal("5000"))
    )
    service.upsert_log(
        db, user.id, HabitLogUpsert(habit_definition_id=habit.id, logged_for_date=d, value=Decimal("8200"))
    )

    logs = service.list_logs(db, user.id, habit_id=habit.id, start=d, end=d)
    assert len(logs.items) == 1
    assert logs.items[0].value == Decimal("8200.000")


def test_upsert_log_404_for_other_users_habit(db: Session, service: HabitService) -> None:
    user_a = UserFactory()
    user_b = UserFactory()
    db.flush()
    habit = service.create_definition(db, user_a.id, HabitDefinitionCreate(name="X", kind=HabitKind.BOOLEAN))

    with pytest.raises(HTTPException) as exc:
        service.upsert_log(
            db,
            user_b.id,
            HabitLogUpsert(habit_definition_id=habit.id, logged_for_date=date(2026, 4, 15), value=Decimal("1")),
        )
    assert exc.value.status_code == 404
