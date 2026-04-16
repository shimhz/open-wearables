"""Tests for InsightsService daily-frame logic.

Focuses on the per-day shape and rollup rules; full wearable-data integration
is covered by the existing repository tests.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from logging import getLogger

import pytest
from sqlalchemy.orm import Session

from app.schemas.enums import HabitKind, ProviderName
from app.schemas.model_crud.eating_event import EatingEventCreate
from app.schemas.model_crud.habit import HabitDefinitionCreate, HabitLogUpsert
from app.schemas.responses.insights import Granularity
from app.services.eating_event_service import EatingEventService
from app.services.habit_service import HabitService
from app.services.insights_service import InsightsService
from app.services.priority_service import PriorityService
from tests.factories import UserFactory


@pytest.fixture
def priority_service() -> PriorityService:
    return PriorityService(log=getLogger(__name__))


@pytest.fixture
def insights(priority_service: PriorityService) -> InsightsService:
    return InsightsService(log=getLogger(__name__), priority_service=priority_service)


@pytest.fixture
def eating(priority_service: PriorityService) -> EatingEventService:
    return EatingEventService(log=getLogger(__name__))


@pytest.fixture
def habits(priority_service: PriorityService) -> HabitService:
    return HabitService(log=getLogger(__name__))


def test_daily_frame_is_dense_when_no_data(db: Session, insights: InsightsService) -> None:
    user = UserFactory()
    db.flush()

    result = insights.get_daily_frame(db, user.id, date(2026, 4, 10), date(2026, 4, 12), Granularity.DAY)

    assert len(result.rows) == 3
    assert [r.date for r in result.rows] == [date(2026, 4, 10), date(2026, 4, 11), date(2026, 4, 12)]
    # Every row is present with nulls — important for charts and correlation alignment.
    assert all(r.sleep.primary_score is None for r in result.rows)
    assert all(r.heart_rate.avg_bpm is None for r in result.rows)
    assert all(r.eating.events_count == 0 for r in result.rows)


def test_eating_windows_and_fasting(db: Session, insights: InsightsService, eating: EatingEventService) -> None:
    user = UserFactory()
    db.flush()

    # Monday: first bite 8:00 UTC, last bite 19:00 UTC.
    eating.create(
        db,
        user.id,
        EatingEventCreate(occurred_at=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)),
    )
    eating.create(
        db,
        user.id,
        EatingEventCreate(occurred_at=datetime(2026, 4, 13, 19, 0, tzinfo=timezone.utc)),
    )
    # Tuesday: first bite 9:00 UTC (14h fast from Monday's 19:00).
    eating.create(
        db,
        user.id,
        EatingEventCreate(occurred_at=datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc)),
    )

    result = insights.get_daily_frame(db, user.id, date(2026, 4, 13), date(2026, 4, 14), Granularity.DAY)

    monday, tuesday = result.rows
    assert monday.eating.events_count == 2
    assert monday.eating.eating_hours == pytest.approx(11.0)
    assert monday.eating.fasting_hours is None  # no prior day logged

    assert tuesday.eating.events_count == 1
    assert tuesday.eating.fasting_hours == pytest.approx(14.0)


def test_habits_use_provided_kind_and_roll_up_weekly(
    db: Session,
    insights: InsightsService,
    habits: HabitService,
) -> None:
    user = UserFactory()
    db.flush()

    meditate = habits.create_definition(db, user.id, HabitDefinitionCreate(name="Meditate", kind=HabitKind.BOOLEAN))
    steps = habits.create_definition(db, user.id, HabitDefinitionCreate(name="Steps", kind=HabitKind.COUNT))

    # 7-day week starting Monday 2026-04-13. Meditate 4/7 days, steps avg across 2 days.
    week_start = date(2026, 4, 13)
    meditate_days = [0, 1, 3, 5]
    for offset in meditate_days:
        habits.upsert_log(
            db,
            user.id,
            HabitLogUpsert(
                habit_definition_id=meditate.id,
                logged_for_date=week_start + timedelta(days=offset),
                value=Decimal("1"),
            ),
        )
    habits.upsert_log(
        db,
        user.id,
        HabitLogUpsert(
            habit_definition_id=steps.id,
            logged_for_date=week_start,
            value=Decimal("6000"),
        ),
    )
    habits.upsert_log(
        db,
        user.id,
        HabitLogUpsert(
            habit_definition_id=steps.id,
            logged_for_date=week_start + timedelta(days=1),
            value=Decimal("10000"),
        ),
    )

    result = insights.get_daily_frame(db, user.id, week_start, week_start + timedelta(days=6), Granularity.WEEK)

    assert len(result.rows) == 1
    week = result.rows[0]
    assert week.date == week_start
    assert week.bucket == Granularity.WEEK

    habit_by_name = {h.name: h for h in week.habits}
    # BOOLEAN rolls up as fraction of days in bucket (4/7 ≈ 0.571)
    assert habit_by_name["Meditate"].value == pytest.approx(Decimal("0.571"), abs=Decimal("0.002"))
    # COUNT rolls up as mean of logged days (6000+10000)/2 = 8000
    assert habit_by_name["Steps"].value == pytest.approx(Decimal("8000"), abs=Decimal("0.1"))


def test_user_provider_priority_picks_sleep_score_winner(
    db: Session,
    insights: InsightsService,
    priority_service: PriorityService,
) -> None:
    """When multiple providers report a sleep score, the user's override wins."""
    from datetime import datetime, timezone
    from uuid import uuid4

    from app.models import HealthScore
    from app.schemas.enums import HealthScoreCategory

    user = UserFactory()
    db.flush()

    # Global: Oura first, Whoop second.
    priority_service.update_provider_priority(db, ProviderName.OURA, 1)
    priority_service.update_provider_priority(db, ProviderName.WHOOP, 2)
    # User override: Whoop wins.
    priority_service.update_user_provider_priority(db, user.id, ProviderName.WHOOP, 1)
    priority_service.update_user_provider_priority(db, user.id, ProviderName.OURA, 2)

    day = date(2026, 4, 13)
    recorded_at = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    for provider, value in [(ProviderName.OURA, Decimal("90")), (ProviderName.WHOOP, Decimal("75"))]:
        db.add(
            HealthScore(
                id=uuid4(),
                user_id=user.id,
                provider=provider,
                category=HealthScoreCategory.SLEEP,
                value=value,
                recorded_at=recorded_at,
                zone_offset="+00:00",
            )
        )
    db.flush()

    result = insights.get_daily_frame(db, user.id, day, day, Granularity.DAY)

    row = result.rows[0]
    assert row.sleep.primary_score is not None
    assert row.sleep.primary_score.provider == ProviderName.WHOOP.value
    assert row.sleep.primary_score.value == Decimal("75.00")
    assert {s.provider for s in row.sleep.all_scores} == {
        ProviderName.OURA.value,
        ProviderName.WHOOP.value,
    }
