"""Insights service: per-day joined frame of sleep, heart-rate, eating, and habits.

Central read-only endpoint that powers correlation screens in the iOS app.
All bucketing is by the user's local date (from the stored per-record
`zone_offset`), so a user who travels still gets each reading on its
actual calendar day.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from logging import Logger, getLogger
from statistics import mean
from uuid import UUID

from app.database import DbSession
from app.models import DataPointSeries, EatingEvent, EventRecord, HealthScore
from app.repositories import (
    DataPointSeriesRepository,
    EatingEventRepository,
    EventRecordRepository,
    HabitDefinitionRepository,
    HabitLogRepository,
    HealthScoreRepository,
)
from app.schemas.enums import HabitKind, HealthScoreCategory
from app.schemas.model_crud.activities import HealthScoreQueryParams
from app.schemas.responses.insights import (
    DailyEating,
    DailyFrameResponse,
    DailyFrameRow,
    DailyHabit,
    DailyHeartRate,
    DailySleep,
    Granularity,
    SleepScore,
)
from app.services.priority_service import PriorityService
from app.utils.exceptions import handle_exceptions


class InsightsService:
    def __init__(self, log: Logger, priority_service: PriorityService | None = None):
        self.logger = log
        self.priority_service = priority_service or PriorityService(log=log)
        self.event_record_repo = EventRecordRepository(EventRecord)
        self.dps_repo = DataPointSeriesRepository(DataPointSeries)
        self.health_score_repo = HealthScoreRepository(HealthScore)
        self.eating_repo = EatingEventRepository()
        self.habit_definition_repo = HabitDefinitionRepository()
        self.habit_log_repo = HabitLogRepository()

    @handle_exceptions
    def get_daily_frame(
        self,
        db_session: DbSession,
        user_id: UUID,
        start: date,
        end: date,
        granularity: Granularity,
    ) -> DailyFrameResponse:
        start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc)

        daily_rows = self._build_daily_rows(db_session, user_id, start, end, start_dt, end_dt)
        rows = self._rollup(daily_rows, granularity) if granularity != Granularity.DAY else daily_rows

        return DailyFrameResponse(
            user_id=user_id,
            start_date=start,
            end_date=end,
            granularity=granularity,
            rows=rows,
        )

    def _build_daily_rows(
        self,
        db_session: DbSession,
        user_id: UUID,
        start: date,
        end: date,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[DailyFrameRow]:
        provider_priority = {
            item.provider.value: item.priority
            for item in self.priority_service.get_effective_user_provider_priorities(db_session, user_id).items
        }

        sleep_by_date = self._reduce_sleep(
            self.event_record_repo.get_sleep_summaries(
                db_session,
                user_id,
                start_dt,
                end_dt,
                cursor=None,
                limit=10_000,
            ),
            provider_priority,
        )
        hr_by_date = self._reduce_hr(
            self.dps_repo.get_daily_hr_aggregates(db_session, user_id, start_dt, end_dt),
            provider_priority,
        )
        scores_by_date = self._collect_sleep_scores(db_session, user_id, start_dt, end_dt, provider_priority)
        eating_by_date = self._build_eating(
            self.eating_repo.list_for_user(db_session, user_id, start_dt, end_dt, order="asc"),
            sleep_by_date,
        )
        habits_by_date = self._collect_habits(db_session, user_id, start, end)

        rows: list[DailyFrameRow] = []
        cursor = start
        while cursor <= end:
            sleep = sleep_by_date.get(cursor, {})
            scores = scores_by_date.get(cursor, [])
            primary = scores[0] if scores else None
            rows.append(
                DailyFrameRow(
                    date=cursor,
                    bucket=Granularity.DAY,
                    sleep=DailySleep(
                        primary_score=primary,
                        all_scores=scores,
                        total_minutes=sleep.get("total_minutes"),
                        deep_minutes=sleep.get("deep_minutes"),
                        rem_minutes=sleep.get("rem_minutes"),
                        light_minutes=sleep.get("light_minutes"),
                        awake_minutes=sleep.get("awake_minutes"),
                        efficiency=sleep.get("efficiency"),
                        source=sleep.get("source"),
                    ),
                    heart_rate=DailyHeartRate(**hr_by_date.get(cursor, {})),
                    eating=eating_by_date.get(cursor, DailyEating()),
                    habits=habits_by_date.get(cursor, []),
                )
            )
            cursor += timedelta(days=1)
        return rows

    @staticmethod
    def _reduce_sleep(
        rows: list[dict],
        provider_priority: dict[str, int],
    ) -> dict[date, dict]:
        """Collapse multi-source sleep rows per date using user provider priority."""
        best: dict[date, tuple[int, dict]] = {}
        for r in rows:
            d = r.get("sleep_date") or r.get("local_date")
            if d is None:
                continue
            source = r.get("source")
            prio = provider_priority.get(source, 999)
            total_seconds = r.get("total_duration") or 0
            cand = {
                "total_minutes": int(total_seconds / 60) if total_seconds else None,
                "deep_minutes": r.get("deep_minutes"),
                "rem_minutes": r.get("rem_minutes"),
                "light_minutes": r.get("light_minutes"),
                "awake_minutes": r.get("awake_minutes"),
                "efficiency": (
                    float(r["efficiency_weighted_sum"]) / float(r["efficiency_duration_sum"])
                    if r.get("efficiency_duration_sum")
                    else None
                ),
                "source": source,
                "min_start_time": r.get("min_start_time"),
            }
            if d not in best or prio < best[d][0]:
                best[d] = (prio, cand)
        return {d: cand for d, (_, cand) in best.items()}

    @staticmethod
    def _reduce_hr(rows: list[dict], provider_priority: dict[str, int]) -> dict[date, dict]:
        best: dict[date, tuple[int, dict]] = {}
        for r in rows:
            d = r["local_date"]
            source = r.get("source")
            prio = provider_priority.get(source, 999)
            cand = {
                "avg_bpm": r.get("hr_avg"),
                "min_bpm": r.get("hr_min"),
                "max_bpm": r.get("hr_max"),
                "resting_bpm": r.get("rhr_avg"),
                "source": source,
            }
            if d not in best or prio < best[d][0]:
                best[d] = (prio, cand)
        return {d: cand for d, (_, cand) in best.items()}

    def _collect_sleep_scores(
        self,
        db_session: DbSession,
        user_id: UUID,
        start_dt: datetime,
        end_dt: datetime,
        provider_priority: dict[str, int],
    ) -> dict[date, list[SleepScore]]:
        params = HealthScoreQueryParams(
            category=HealthScoreCategory.SLEEP,
            start_datetime=start_dt,
            end_datetime=end_dt,
            limit=10_000,
            offset=0,
        )
        scores, _total = self.health_score_repo.get_with_filters(db_session, user_id, params)

        by_date: dict[date, dict[str, SleepScore]] = defaultdict(dict)
        for s in scores:
            local_d = self._to_local_date(s.recorded_at, s.zone_offset)
            provider = s.provider.value
            # If the same provider reports twice (rare), keep the later recorded_at.
            existing = by_date[local_d].get(provider)
            if existing is None:
                by_date[local_d][provider] = SleepScore(provider=provider, value=s.value)

        return {
            d: sorted(
                providers.values(),
                key=lambda sc: provider_priority.get(sc.provider, 999),
            )
            for d, providers in by_date.items()
        }

    @staticmethod
    def _build_eating(
        events: Iterable[EatingEvent],
        sleep_by_date: dict[date, dict],
    ) -> dict[date, DailyEating]:
        by_date: dict[date, list[EatingEvent]] = defaultdict(list)
        for e in events:
            local_d = InsightsService._to_local_date(e.occurred_at, e.zone_offset)
            by_date[local_d].append(e)

        ordered_dates = sorted(by_date.keys())
        prior_last_bite: datetime | None = None
        out: dict[date, DailyEating] = {}
        for d in ordered_dates:
            day_events = sorted(by_date[d], key=lambda x: x.occurred_at)
            first = day_events[0].occurred_at
            last = day_events[-1].occurred_at
            eating_hours = (last - first).total_seconds() / 3600 if len(day_events) > 1 else 0.0
            fasting_hours = (first - prior_last_bite).total_seconds() / 3600 if prior_last_bite is not None else None
            sleep = sleep_by_date.get(d + timedelta(days=1)) or sleep_by_date.get(d)
            last_to_sleep = None
            sleep_start = sleep.get("min_start_time") if sleep else None
            if sleep_start is not None and sleep_start > last:
                last_to_sleep = int((sleep_start - last).total_seconds() / 60)

            out[d] = DailyEating(
                first_bite_at=first,
                last_bite_at=last,
                eating_hours=round(eating_hours, 2),
                fasting_hours=round(fasting_hours, 2) if fasting_hours is not None else None,
                events_count=len(day_events),
                last_bite_to_sleep_start_minutes=last_to_sleep,
            )
            prior_last_bite = last
        return out

    def _collect_habits(
        self,
        db_session: DbSession,
        user_id: UUID,
        start: date,
        end: date,
    ) -> dict[date, list[DailyHabit]]:
        definitions = {
            h.id: h for h in self.habit_definition_repo.list_for_user(db_session, user_id, include_archived=True)
        }
        logs = self.habit_log_repo.list_for_user(db_session, user_id, None, start, end)
        out: dict[date, list[DailyHabit]] = defaultdict(list)
        for log in logs:
            habit = definitions.get(log.habit_definition_id)
            if habit is None:
                continue
            out[log.logged_for_date].append(
                DailyHabit(id=habit.id, name=habit.name, kind=habit.kind, value=log.value),
            )
        return out

    @staticmethod
    def _to_local_date(dt: datetime, zone_offset: str | None) -> date:
        """Convert a UTC datetime + '+HH:MM' offset into the local calendar date."""
        if zone_offset is None:
            return dt.date()
        try:
            sign = 1 if zone_offset[0] == "+" else -1
            hours, minutes = zone_offset[1:].split(":")
            delta = timedelta(hours=int(hours), minutes=int(minutes)) * sign
        except (IndexError, ValueError):
            return dt.date()
        return (dt + delta).date()

    def _rollup(
        self,
        daily_rows: list[DailyFrameRow],
        granularity: Granularity,
    ) -> list[DailyFrameRow]:
        buckets: dict[date, list[DailyFrameRow]] = defaultdict(list)
        for row in daily_rows:
            buckets[self._bucket_start(row.date, granularity)].append(row)

        out: list[DailyFrameRow] = []
        for bucket_start in sorted(buckets.keys()):
            rows = buckets[bucket_start]
            out.append(self._aggregate_bucket(bucket_start, granularity, rows))
        return out

    @staticmethod
    def _bucket_start(d: date, g: Granularity) -> date:
        if g == Granularity.WEEK:
            return d - timedelta(days=d.weekday())  # Monday start
        if g == Granularity.MONTH:
            return d.replace(day=1)
        if g == Granularity.YEAR:
            return d.replace(month=1, day=1)
        return d

    @staticmethod
    def _avg(values: list[float | int | None]) -> float | None:
        real = [float(v) for v in values if v is not None]
        return mean(real) if real else None

    def _aggregate_bucket(
        self,
        bucket_start: date,
        granularity: Granularity,
        rows: list[DailyFrameRow],
    ) -> DailyFrameRow:
        sleep = DailySleep(
            total_minutes=int(self._avg([r.sleep.total_minutes for r in rows]) or 0) or None,
            deep_minutes=int(self._avg([r.sleep.deep_minutes for r in rows]) or 0) or None,
            rem_minutes=int(self._avg([r.sleep.rem_minutes for r in rows]) or 0) or None,
            light_minutes=int(self._avg([r.sleep.light_minutes for r in rows]) or 0) or None,
            awake_minutes=int(self._avg([r.sleep.awake_minutes for r in rows]) or 0) or None,
            efficiency=self._avg([r.sleep.efficiency for r in rows]),
            primary_score=self._avg_primary_score(rows),
            all_scores=[],
        )
        heart_rate = DailyHeartRate(
            avg_bpm=self._avg([r.heart_rate.avg_bpm for r in rows]),
            min_bpm=self._avg([r.heart_rate.min_bpm for r in rows]),
            max_bpm=self._avg([r.heart_rate.max_bpm for r in rows]),
            resting_bpm=self._avg([r.heart_rate.resting_bpm for r in rows]),
        )
        eating = DailyEating(
            eating_hours=self._avg([r.eating.eating_hours for r in rows]),
            fasting_hours=self._avg([r.eating.fasting_hours for r in rows]),
            events_count=int(self._avg([r.eating.events_count for r in rows]) or 0),
            last_bite_to_sleep_start_minutes=(
                int(self._avg([r.eating.last_bite_to_sleep_start_minutes for r in rows]) or 0) or None
            ),
        )
        habits = self._aggregate_habits(rows)
        return DailyFrameRow(
            date=bucket_start,
            bucket=granularity,
            sleep=sleep,
            heart_rate=heart_rate,
            eating=eating,
            habits=habits,
        )

    @staticmethod
    def _avg_primary_score(rows: list[DailyFrameRow]) -> SleepScore | None:
        values = [
            float(r.sleep.primary_score.value)
            for r in rows
            if r.sleep.primary_score is not None and r.sleep.primary_score.value is not None
        ]
        if not values:
            return None
        # Attribute the averaged score to whichever provider won most days.
        providers = [r.sleep.primary_score.provider for r in rows if r.sleep.primary_score is not None]
        top_provider = max(set(providers), key=providers.count) if providers else "unknown"
        return SleepScore(provider=top_provider, value=Decimal(str(round(mean(values), 2))))

    def _aggregate_habits(self, rows: list[DailyFrameRow]) -> list[DailyHabit]:
        by_id: dict[UUID, list[DailyHabit]] = defaultdict(list)
        for r in rows:
            for h in r.habits:
                by_id[h.id].append(h)

        habits: list[DailyHabit] = []
        for habit_id, entries in by_id.items():
            first = entries[0]
            values = [h.value for h in entries]
            if first.kind == HabitKind.BOOLEAN:
                pct = sum(1 for v in values if v >= Decimal("1")) / max(len(rows), 1)
                agg = Decimal(str(round(pct, 3)))
            elif first.kind == HabitKind.COUNT:
                agg = Decimal(str(round(sum(float(v) for v in values) / max(len(values), 1), 3)))
            else:
                agg = Decimal(str(round(mean(float(v) for v in values), 3)))
            habits.append(DailyHabit(id=habit_id, name=first.name, kind=first.kind, value=agg))
        return habits


insights_service = InsightsService(log=getLogger(__name__))
