import json
from pathlib import Path

USER_DATA_PATH = Path(__file__).resolve().parent.parent / "db" / "user_data.json"


def load_user_data():
    with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_daily_entry(user_data):
    daily_data = user_data.get("daily_data", [])
    if not daily_data:
        return None
    return daily_data[-1]


def get_recent_daily_context(user_data, days=3):
    daily_data = user_data.get("daily_data", [])
    return daily_data[-days:]
