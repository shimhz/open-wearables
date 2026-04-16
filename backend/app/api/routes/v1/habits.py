"""API endpoints for user habit definitions and daily habit logs."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, status

from app.database import DbSession
from app.schemas.model_crud.habit import (
    HabitDefinitionCreate,
    HabitDefinitionListResponse,
    HabitDefinitionResponse,
    HabitDefinitionUpdate,
    HabitLogListResponse,
    HabitLogResponse,
    HabitLogUpsert,
)
from app.services import ApiKeyDep, habit_service

router = APIRouter()


@router.get(
    "/users/{user_id}/habits",
    summary="List a user's habits",
)
def list_habits(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    include_archived: Annotated[bool, Query()] = False,
) -> HabitDefinitionListResponse:
    return habit_service.list_definitions(db, user_id, include_archived)


@router.post(
    "/users/{user_id}/habits",
    status_code=status.HTTP_201_CREATED,
    summary="Create a habit definition",
)
def create_habit(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    payload: HabitDefinitionCreate,
) -> HabitDefinitionResponse:
    return habit_service.create_definition(db, user_id, payload)


@router.patch(
    "/users/{user_id}/habits/{habit_id}",
    summary="Update habit definition (rename, archive, change unit)",
)
def update_habit(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    habit_id: Annotated[UUID, Path(description="Habit ID")],
    payload: HabitDefinitionUpdate,
) -> HabitDefinitionResponse:
    return habit_service.update_definition(db, user_id, habit_id, payload)


@router.get(
    "/users/{user_id}/habit-logs",
    summary="List habit log entries",
)
def list_habit_logs(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    habit_id: Annotated[UUID | None, Query()] = None,
    start: Annotated[date | None, Query(description="Inclusive lower bound on logged_for_date")] = None,
    end: Annotated[date | None, Query(description="Inclusive upper bound on logged_for_date")] = None,
) -> HabitLogListResponse:
    return habit_service.list_logs(db, user_id, habit_id, start, end)


@router.put(
    "/users/{user_id}/habit-logs",
    summary="Upsert a habit log for one day",
)
def upsert_habit_log(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    payload: HabitLogUpsert,
) -> HabitLogResponse:
    return habit_service.upsert_log(db, user_id, payload)
