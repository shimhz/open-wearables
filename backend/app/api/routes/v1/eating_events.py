"""API endpoints for user eating events (meal timestamps)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, status

from app.database import DbSession
from app.schemas.model_crud.eating_event import (
    EatingEventCreate,
    EatingEventListResponse,
    EatingEventResponse,
    EatingEventUpdate,
)
from app.services import ApiKeyDep, eating_event_service

router = APIRouter()


@router.get(
    "/users/{user_id}/eating-events",
    summary="List a user's eating events",
)
def list_eating_events(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    start: Annotated[datetime | None, Query(description="Inclusive lower bound on occurred_at")] = None,
    end: Annotated[datetime | None, Query(description="Exclusive upper bound on occurred_at")] = None,
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
) -> EatingEventListResponse:
    return eating_event_service.list_for_user(db, user_id, start, end, order)


@router.post(
    "/users/{user_id}/eating-events",
    status_code=status.HTTP_201_CREATED,
    summary="Log one eating event",
)
def create_eating_event(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    payload: EatingEventCreate,
) -> EatingEventResponse:
    return eating_event_service.create(db, user_id, payload)


@router.patch(
    "/users/{user_id}/eating-events/{event_id}",
    summary="Edit a logged eating event",
)
def update_eating_event(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    event_id: Annotated[UUID, Path(description="Eating event ID")],
    payload: EatingEventUpdate,
) -> EatingEventResponse:
    return eating_event_service.update(db, user_id, event_id, payload)


@router.delete(
    "/users/{user_id}/eating-events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an eating event",
)
def delete_eating_event(
    db: DbSession,
    _api_key: ApiKeyDep,
    user_id: Annotated[UUID, Path(description="User ID")],
    event_id: Annotated[UUID, Path(description="Eating event ID")],
) -> None:
    eating_event_service.delete(db, user_id, event_id)
