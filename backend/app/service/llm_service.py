from backend.app.mcp_server.models.cycle_prediction import get_next_date
from backend.app.mcp_server.models.nutrition_calculator import (
    food_list,
    nutrition_calculator,
)
from backend.app.mcp_server.models.prediction_model import predict_fatigue_and_mood
from backend.app.utils.llm_client import call_llm
from backend.app.utils.rag_store import hybrid_search
from backend.app.utils.user_context import (
    get_latest_daily_entry,
    get_recent_daily_context,
    load_user_data,
)


NUTRITION_COL_MAP = {
    "Carbohydrates (g)": "carbs_g",
    "Protein (g)": "protein_g",
    "Fats (g)": "fats_g",
    "Free Sugar (g)": "free_sugar_g",
    "Fibre (g)": "fibre_g",
    "Sodium (mg)": "sodium_mg",
    "Calcium (mg)": "calcium_mg",
    "Iron (mg)": "iron_mg",
    "Vitamin C (mg)": "vitamin_c_mg",
    "Folate (µg)": "folate_ug",
}


def parse_food(food_text: str) -> dict:
    food_items = [
        food_list(item=item.strip(), quantity=100)
        for item in food_text.split(",")
        if item.strip()
    ]
    results = nutrition_calculator(food_items)
    nutrients = {value: 0 for value in NUTRITION_COL_MAP.values()}

    for result in results:
        if not result.get("found"):
            continue

        nutrition = result.get("nutrition", {})
        for source_key, target_key in NUTRITION_COL_MAP.items():
            nutrients[target_key] = round(
                nutrients[target_key] + float(nutrition.get(source_key, 0)),
                2,
            )

    return nutrients


def find_missing_fields(user_data, latest_day):
    missing = []

    if not user_data.get("last_period_date"):
        missing.append("last_period_date")

    if latest_day is None:
        missing.append("daily_data")
        return missing

    if latest_day.get("sleep_hours") in [None, ""]:
        missing.append("sleep_hours")

    if latest_day.get("stress_level") in [None, ""]:
        missing.append("stress_level")

    if not latest_day.get("food_intake"):
        missing.append("food_intake")

    return missing


def build_prediction_context(user_data, latest_day):
    cycle = get_next_date(user_data["last_period_date"])

    food_text = ", ".join(latest_day.get("food_intake", []))
    nutrients = latest_day.get("nutrients")

    if not nutrients:
        nutrients = parse_food(food_text)

    features = {
        "cycle_phase": cycle["cycle_phase"],
        "sleep_hours": float(latest_day["sleep_hours"]),
        "stress_level": int(latest_day["stress_level"]),
        **nutrients,
    }

    prediction = predict_fatigue_and_mood(features)

    return cycle, nutrients, features, prediction


def ask_assistant(question: str):
    user_data = load_user_data()
    latest_day = get_latest_daily_entry(user_data)
    recent_days = get_recent_daily_context(user_data, days=3)

    missing = find_missing_fields(user_data, latest_day)

    if missing:
        return {
            "type": "follow_up",
            "missing_fields": missing,
            "answer": make_missing_data_question(missing),
        }

    cycle, nutrients, features, prediction = build_prediction_context(user_data, latest_day)

    rag_query = f"""
    Question: {question}
    Cycle phase: {cycle.get("cycle_phase")}
    Mood prediction: {prediction.get("mood_state")}
    Fatigue prediction: {prediction.get("fatigue_level")}
    Dominant factor: {prediction.get("dominant_factor")}
    Symptoms: {latest_day.get("symptoms")}
    Mood note: {latest_day.get("mood_note")}
    """

    rag_results = hybrid_search(rag_query, top_k=4)

    rag_context = "\n\n".join(
        f"Source: {item['source']}\n{item['text']}"
        for item in rag_results
    )

    messages = [
        {
            "role": "system",
            "content": """
You are Bloom, a supportive menstrual wellness assistant.

Your job:
- Answer using the user's cycle data, daily logs, ML prediction, and retrieved scientific context.
- Be friendly and conversational.
- Explain fatigue level, mood state, and likely contributing factors clearly.
- Ask a follow-up question if more information is needed.
- Do not diagnose medical conditions.
- Do not claim medical certainty.
- Encourage professional care for severe, persistent, or concerning symptoms.

Keep the response concise and user-friendly.
"""
        },
        {
            "role": "user",
            "content": f"""
User question:
{question}

User profile:
Name: {user_data.get("name")}
Age: {user_data.get("age")}
Last period date: {user_data.get("last_period_date")}
Average cycle length: {user_data.get("average_cycle_length")}
Average period length: {user_data.get("average_period_length")}

Recent daily data:
{recent_days}

Computed cycle:
{cycle}

Nutrition features:
{nutrients}

ML features:
{features}

ML prediction:
{prediction}

Retrieved scientific context:
{rag_context}

Now respond as a helpful chatbot.
"""
        }
    ]

    answer = call_llm(messages)

    return {
        "type": "answer",
        "answer": answer,
        "cycle": cycle,
        "prediction": prediction,
        "rag_sources": [
            {"source": item["source"], "score": item["score"]}
            for item in rag_results
        ],
    }


def make_missing_data_question(missing):
    friendly_names = {
        "last_period_date": "your last period date",
        "daily_data": "today's daily log",
        "sleep_hours": "how many hours you slept",
        "stress_level": "your stress level from 1 to 5",
        "food_intake": "what you ate today",
    }

    readable = [friendly_names.get(field, field) for field in missing]

    return (
        "I need a little more info before I can give a useful answer. "
        f"Can you tell me {', '.join(readable)}?"
    )
