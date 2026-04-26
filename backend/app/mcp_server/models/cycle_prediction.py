######## create next period date here
import json
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "user_data.json"

DEFAULT_MENSTRUAL_DAYS = 5
DEFAULT_FOLLICULAR_DAYS = 11
DEFAULT_OVULATION_DAYS = 15
DEFAULT_LUTEAL_DAYS = 28


def _to_positive_int(value, default: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default

    return value if value > 0 else default


def _load_cycle_days() -> tuple[int, int]:
    if not DB_PATH.exists():
        return DEFAULT_MENSTRUAL_DAYS, DEFAULT_LUTEAL_DAYS

    with open(DB_PATH, "r", encoding="utf-8") as f:
        user_data = json.load(f)

    menstrual_days = _to_positive_int(
        user_data.get("menstrual_days", user_data.get("average_period_length")),
        DEFAULT_MENSTRUAL_DAYS,
    )
    luteal_days = _to_positive_int(
        user_data.get(
            "luteal_days",
            user_data.get("average_cycle_length", user_data.get("average_cycle_length")),
        ),
        DEFAULT_LUTEAL_DAYS,
    )

    return menstrual_days, luteal_days


def get_next_date(date_in: str):
    today = datetime.today()
    last_date = datetime.strptime(date_in, "%Y-%m-%d")
    menstrual_days, luteal_days = _load_cycle_days()
    
    day_since = (today - last_date).days
    cycle_day = (day_since % luteal_days) + 1
    
    if cycle_day <= menstrual_days:
        phase = "menstrual"
    elif cycle_day <= DEFAULT_FOLLICULAR_DAYS:
        phase = "follicular"
    elif cycle_day <= DEFAULT_OVULATION_DAYS:
        phase = "ovulation"
    else:
        phase = "luteal"
    
    next_period = last_date + timedelta(days=luteal_days)

    
    return {
        "days_since": day_since,
        "cycle_day": cycle_day,
        "cycle_phase": phase,
        "next_period_date": next_period.date()
    }
