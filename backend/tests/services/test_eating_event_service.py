"""Tests for EatingEventService."""

from datetime import datetime, timedelta, timezone
from logging import getLogger

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.model_crud.eating_event import EatingEventCreate, EatingEventUpdate
from app.services.eating_event_service import EatingEventService
from tests.factories import UserFactory


@pytest.fixture
def service() -> EatingEventService:
    return EatingEventService(log=getLogger(__name__))


def test_create_and_list_returns_events_in_order(db: Session, service: EatingEventService) -> None:
    user = UserFactory()
    db.flush()
    t0 = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)

    service.create(db, user.id, EatingEventCreate(occurred_at=t0 + timedelta(hours=2), label="lunch"))
    service.create(db, user.id, EatingEventCreate(occurred_at=t0, label="breakfast"))

    result = service.list_for_user(db, user.id, start=None, end=None, order="asc")
    labels = [e.label for e in result.items]
    assert labels == ["breakfast", "lunch"]


def test_list_filters_by_time_range(db: Session, service: EatingEventService) -> None:
    user = UserFactory()
    db.flush()
    t0 = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)

    service.create(db, user.id, EatingEventCreate(occurred_at=t0, label="a"))
    service.create(db, user.id, EatingEventCreate(occurred_at=t0 + timedelta(days=1), label="b"))
    service.create(db, user.id, EatingEventCreate(occurred_at=t0 + timedelta(days=2), label="c"))

    result = service.list_for_user(
        db,
        user.id,
        start=t0 + timedelta(hours=1),
        end=t0 + timedelta(days=2),
        order="asc",
    )
    assert [e.label for e in result.items] == ["b"]


def test_update_patches_fields(db: Session, service: EatingEventService) -> None:
    user = UserFactory()
    db.flush()
    created = service.create(
        db, user.id, EatingEventCreate(occurred_at=datetime(2026, 4, 15, tzinfo=timezone.utc), label="lunch")
    )

    updated = service.update(db, user.id, created.id, EatingEventUpdate(label="brunch", notes="pancakes"))

    assert updated.label == "brunch"
    assert updated.notes == "pancakes"
    assert updated.occurred_at == created.occurred_at


def test_delete_404_for_other_user(db: Session, service: EatingEventService) -> None:
    user_a = UserFactory()
    user_b = UserFactory()
    db.flush()
    created = service.create(db, user_a.id, EatingEventCreate(occurred_at=datetime(2026, 4, 15, tzinfo=timezone.utc)))

    with pytest.raises(HTTPException) as exc:
        service.delete(db, user_b.id, created.id)
    assert exc.value.status_code == 404
