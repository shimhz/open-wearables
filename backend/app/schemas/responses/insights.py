from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import HabitKind


class Granularity(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class SleepScore(BaseModel):
    """A single provider's sleep score for a day."""

    provider: str
    value: Decimal | None = None


class DailySleep(BaseModel):
    primary_score: SleepScore | None = None  # winner per user's effective provider priority
    all_scores: list[SleepScore] = []  # every provider that reported a score for this day
    total_minutes: int | None = None
    deep_minutes: int | None = None
    rem_minutes: int | None = None
    light_minutes: int | None = None
    awake_minutes: int | None = None
    efficiency: float | None = None
    source: str | None = None  # the data source (provider) whose stage breakdown we used


class DailyHeartRate(BaseModel):
    resting_bpm: float | None = None
    avg_bpm: float | None = None
    min_bpm: float | None = None
    max_bpm: float | None = None
    source: str | None = None


class DailyEating(BaseModel):
    first_bite_at: datetime | None = None
    last_bite_at: datetime | None = None
    eating_hours: float | None = None
    fasting_hours: float | None = None  # gap from prior day's last bite to this day's first bite
    events_count: int = 0
    last_bite_to_sleep_start_minutes: int | None = None


class DailyHabit(BaseModel):
    id: UUID
    name: str
    kind: HabitKind
    value: Decimal


class DailyFrameRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    bucket: Granularity
    sleep: DailySleep
    heart_rate: DailyHeartRate
    eating: DailyEating
    habits: list[DailyHabit]


class DailyFrameResponse(BaseModel):
    user_id: UUID
    start_date: date
    end_date: date
    granularity: Granularity
    rows: list[DailyFrameRow]
