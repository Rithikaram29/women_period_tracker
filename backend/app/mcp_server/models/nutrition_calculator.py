from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process


class food_list(BaseModel):
    item: str
    quantity: int = Field(gt=0)


DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "Indian_Food_Nutrition_Processed.csv"
)
df = pd.read_csv(DATASET_PATH)
df["_normalized_dish_name"] = df["Dish Name"].astype(str).str.lower().str.strip()
NUTRITION_COLUMNS = [
    column
    for column in df.columns
    if column not in {"Dish Name", "_normalized_dish_name"}
]


def nutrition_calculator(food_items: list[food_list]) -> list[dict[str, Any]]:
    """Return scaled nutrition data for matched items, or suggestions when no exact match exists."""
    if not food_items:
        return []

    results: list[dict[str, Any]] = []
    for food in food_items:
        match = find_food_row(food.item, df)
        if match["match"] is None:
            results.append(
                {
                    "item": food.item,
                    "quantity": food.quantity,
                    "found": False,
                    "suggestions": match["suggestions"],
                }
            )
            continue

        row = match["match"]
        nutrition = {
            column: round(float(row[column]) * food.quantity, 2)
            for column in NUTRITION_COLUMNS
        }
        results.append(
            {
                "item": food.item,
                "matched_item": row["Dish Name"],
                "quantity": food.quantity,
                "found": True,
                "nutrition": nutrition,
            }
        )

    return results


def find_food_row(food: str, dataset: pd.DataFrame) -> dict[str, Any]:
    normalized_food = food.lower().strip()
    exact_matches = dataset[dataset["_normalized_dish_name"] == normalized_food]

    if not exact_matches.empty:
        return {"match": exact_matches.iloc[0], "suggestions": []}

    options = process.extract(
        normalized_food,
        dataset["_normalized_dish_name"],
        scorer=fuzz.WRatio,
        limit=4,
    )

    suggestions: list[str] = []
    for _, score, index in options:
        if score == 100:
            return {"match": dataset.iloc[index], "suggestions": []}

        suggestion = str(dataset.iloc[index]["Dish Name"])
        if suggestion not in suggestions:
            suggestions.append(suggestion)

    return {"match": None, "suggestions": suggestions}
