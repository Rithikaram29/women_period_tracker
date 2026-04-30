from mcp.server.fastmcp import FastMCP

from models.cycle_prediction import get_next_date
from models.nutrition_calculator import food_list, nutrition_calculator
from models.prediction_model import predict_fatigue_and_mood

mcp = FastMCP("menstrual-health-ai")

_COL_MAP = {
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


def _parse_food_text(food_text: str) -> list[food_list]:
    return [food_list(item=item.strip(), quantity=100) for item in food_text.split(",") if item.strip()]


def _aggregate_nutrition(results: list) -> dict:
    totals: dict = {}
    for r in results:
        if r.get("found"):
            for col, key in _COL_MAP.items():
                totals[key] = round(totals.get(key, 0) + r["nutrition"].get(col, 0), 2)
    return totals


@mcp.tool()
def get_cycle_features(last_period_date: str) -> dict:
    """
    Compute menstrual cycle features from last period date.
    Date format: YYYY-MM-DD
    """
    return get_next_date(last_period_date)


@mcp.tool()
def get_nutrition_features(food_text: str) -> list:
    """
    Convert free-text food intake into structured nutrition features.
    Example: 'rice, dal, curd'
    """
    return nutrition_calculator(_parse_food_text(food_text))


@mcp.tool()
def predict_fatigue_mood(
    last_period_date: str,
    sleep_hours: float,
    stress_level: int,
    food_text: str
) -> dict:
    """
    Predict fatigue level and mood state from cycle, lifestyle, and nutrition inputs.
    """
    cycle_data = get_next_date(last_period_date)
    nutrition_results = nutrition_calculator(_parse_food_text(food_text))
    nutrition = _aggregate_nutrition(nutrition_results)

    features = {
        "cycle_phase": cycle_data["cycle_phase"],
        "sleep_hours": sleep_hours,
        "stress_level": stress_level,
        "carbs_g": nutrition.get("carbs_g", 0),
        "protein_g": nutrition.get("protein_g", 0),
        "fats_g": nutrition.get("fats_g", 0),
        "free_sugar_g": nutrition.get("free_sugar_g", 0),
        "fibre_g": nutrition.get("fibre_g", 0),
        "sodium_mg": nutrition.get("sodium_mg", 0),
        "calcium_mg": nutrition.get("calcium_mg", 0),
        "iron_mg": nutrition.get("iron_mg", 0),
        "vitamin_c_mg": nutrition.get("vitamin_c_mg", 0),
        "folate_ug": nutrition.get("folate_ug", 0),
    }

    prediction = predict_fatigue_and_mood(features)

    return {
        "cycle_phase": cycle_data["cycle_phase"],
        "next_period_date": cycle_data["next_period_date"],
        "nutrition": nutrition_results,
        "prediction": prediction
    }


if __name__ == "__main__":
    mcp.run()
