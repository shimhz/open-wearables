"""Tests for user-scoped provider priority methods on PriorityService."""

from logging import getLogger

import pytest
from sqlalchemy.orm import Session

from app.schemas.enums import ProviderName
from app.schemas.model_crud.data_priority import (
    UserProviderPriorityBase,
    UserProviderPriorityBulkUpdate,
)
from app.services.priority_service import PriorityService
from tests.factories import UserFactory


@pytest.fixture
def priority_service() -> PriorityService:
    return PriorityService(log=getLogger(__name__))


def test_effective_order_is_global_when_no_overrides(db: Session, priority_service: PriorityService) -> None:
    user = UserFactory()
    db.flush()

    priority_service.update_provider_priority(db, ProviderName.OURA, 1)
    priority_service.update_provider_priority(db, ProviderName.WHOOP, 2)

    result = priority_service.get_effective_user_provider_priorities(db, user.id)

    assert [(i.provider, i.priority, i.source) for i in result.items] == [
        (ProviderName.OURA, 1, "global"),
        (ProviderName.WHOOP, 2, "global"),
    ]


def test_user_override_wins_over_global(db: Session, priority_service: PriorityService) -> None:
    user = UserFactory()
    db.flush()

    priority_service.update_provider_priority(db, ProviderName.OURA, 1)
    priority_service.update_provider_priority(db, ProviderName.WHOOP, 2)
    priority_service.update_user_provider_priority(db, user.id, ProviderName.WHOOP, 1)
    priority_service.update_user_provider_priority(db, user.id, ProviderName.OURA, 5)

    result = priority_service.get_effective_user_provider_priorities(db, user.id)

    by_provider = {i.provider: i for i in result.items}
    assert by_provider[ProviderName.WHOOP].priority == 1
    assert by_provider[ProviderName.WHOOP].source == "user"
    assert by_provider[ProviderName.OURA].priority == 5
    assert by_provider[ProviderName.OURA].source == "user"
    assert result.items[0].provider == ProviderName.WHOOP


def test_reset_removes_user_override(db: Session, priority_service: PriorityService) -> None:
    user = UserFactory()
    db.flush()

    priority_service.update_provider_priority(db, ProviderName.OURA, 1)
    priority_service.update_user_provider_priority(db, user.id, ProviderName.OURA, 9)

    result = priority_service.reset_user_provider_priority(db, user.id, ProviderName.OURA)

    oura = next(i for i in result.items if i.provider == ProviderName.OURA)
    assert oura.priority == 1
    assert oura.source == "global"


def test_bulk_update_returns_effective_order(db: Session, priority_service: PriorityService) -> None:
    user = UserFactory()
    db.flush()

    priority_service.update_provider_priority(db, ProviderName.OURA, 3)

    result = priority_service.bulk_update_user_provider_priorities(
        db,
        user.id,
        UserProviderPriorityBulkUpdate(
            priorities=[
                UserProviderPriorityBase(provider=ProviderName.WHOOP, priority=1),
                UserProviderPriorityBase(provider=ProviderName.OURA, priority=2),
            ]
        ),
    )

    assert [(i.provider, i.priority) for i in result.items] == [
        (ProviderName.WHOOP, 1),
        (ProviderName.OURA, 2),
    ]
