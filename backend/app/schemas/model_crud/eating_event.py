from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EatingEventCreate(BaseModel):
    occurred_at: datetime
    zone_offset: str | None = Field(None, max_length=10)
    label: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=255)


class EatingEventUpdate(BaseModel):
    occurred_at: datetime | None = None
    zone_offset: str | None = Field(None, max_length=10)
    label: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=255)


class EatingEventResponse(BaseModel):
    id: UUID
    user_id: UUID
    occurred_at: datetime
    zone_offset: str | None
    label: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EatingEventListResponse(BaseModel):
    items: list[EatingEventResponse]
