from enum import Enum


class HabitKind(str, Enum):
    """Controls how `habit_log.value` is interpreted and rolled up.

    - BOOLEAN: 0 or 1. Rolls up as % of days completed.
    - COUNT: non-negative integer (stored as decimal). Rolls up as sum.
    - DURATION_MIN: minutes. Rolls up as mean per day.
    - SCALE_1_5: subjective rating. Rolls up as mean.
    - NUMERIC: anything else with a unit. Rolls up as mean.
    """

    BOOLEAN = "boolean"
    COUNT = "count"
    DURATION_MIN = "duration_min"
    SCALE_1_5 = "scale_1_5"
    NUMERIC = "numeric"
