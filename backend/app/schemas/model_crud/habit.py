from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.enums import HabitKind


class HabitDefinitionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    kind: HabitKind
    unit: str | None = Field(None, max_length=20)


class HabitDefinitionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    unit: str | None = Field(None, max_length=20)
    archived: bool | None = None


class HabitDefinitionResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    kind: HabitKind
    unit: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HabitDefinitionListResponse(BaseModel):
    items: list[HabitDefinitionResponse]


class HabitLogUpsert(BaseModel):
    habit_definition_id: UUID
    logged_for_date: date
    value: Decimal
    zone_offset: str | None = Field(None, max_length=10)


class HabitLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    habit_definition_id: UUID
    logged_for_date: date
    value: Decimal
    logged_at: datetime
    zone_offset: str | None

    model_config = {"from_attributes": True}


class HabitLogListResponse(BaseModel):
    items: list[HabitLogResponse]
