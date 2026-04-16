"""Insights endpoint: per-day joined sleep / HR / eating / habits frame."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from app.database import DbSession
from app.schemas.responses.insights import DailyFrameResponse, Granularity
from app.services import ApiKeyDep
from app.services.insights_service import insights_service

router = APIRouter()


@router.get(
    "/users/{user_id}/insights/daily-frame",
    summary="Per-day joined frame of sleep, heart rate, eating, and habits",
)
def get_daily_frame(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    start_date: Annotated[date, Query(description="Inclusive lower bound (local date)")],
    end_date: Annotated[date, Query(description="Inclusive upper bound (local date)")],
    granularity: Annotated[Granularity, Query()] = Granularity.DAY,
) -> DailyFrameResponse:
    """Dense rows over [start_date, end_date] for a user.

    Each row contains sleep metrics + all provider sleep scores (primary picked by
    the user's effective provider priority), heart-rate aggregates, derived eating
    windows (first/last bite, eating/fasting hours, last-bite-to-sleep gap), and
    every habit with its value for that day.

    Granularity:
    - `day`: one row per calendar day (default)
    - `week`: Monday-start weeks; numeric fields averaged, boolean habits become
      "% of days completed"
    - `month`, `year`: analogous, bucketed by first day of month/year
    """
    return insights_service.get_daily_frame(db, user_id, start_date, end_date, granularity)
