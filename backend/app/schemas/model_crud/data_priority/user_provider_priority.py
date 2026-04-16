from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.enums import ProviderName


class UserProviderPriorityBase(BaseModel):
    provider: ProviderName
    priority: int = Field(..., ge=1, le=100)


class UserProviderPriorityUpdate(BaseModel):
    priority: int = Field(..., ge=1, le=100)


class UserProviderPriorityResponse(UserProviderPriorityBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProviderPriorityBulkUpdate(BaseModel):
    priorities: list[UserProviderPriorityBase]


class EffectiveProviderPriorityItem(BaseModel):
    """One provider in the user's effective ordering.

    `source` indicates whether the priority came from a user override
    or the global default, so the iOS app can show "using default".
    """

    provider: ProviderName
    priority: int
    source: str  # "user" | "global"


class EffectiveProviderPriorityListResponse(BaseModel):
    items: list[EffectiveProviderPriorityItem]
