import random
from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

CYCLE_PHASES = ["menstrual", "follicular", "ovulation", "luteal"]
MOODS = ["happy", "sad", "anxious", "groggy"]


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def generate_nutrition_values():
    """
    Approximate daily/meal-level nutrition-like values for prototype data.
    These are not medical targets.
    """
    return {
        "carbs_g": round(random.uniform(40, 220), 1),
        "protein_g": round(random.uniform(5, 70), 1),
        "fats_g": round(random.uniform(5, 80), 1),
        "free_sugar_g": round(random.uniform(0, 70), 1),
        "fibre_g": round(random.uniform(1, 35), 1),
        "sodium_mg": round(random.uniform(100, 3000), 1),
        "calcium_mg": round(random.uniform(50, 1200), 1),
        "iron_mg": round(random.uniform(0.5, 25), 1),
        "vitamin_c_mg": round(random.uniform(0, 150), 1),
        "folate_ug": round(random.uniform(20, 600), 1),
    }


def compute_fatigue_level(row):
    fatigue_score = 2.5

    # Strong behavioral signals
    if row["sleep_hours"] < 5:
        fatigue_score += 1.4
    elif row["sleep_hours"] < 6.5:
        fatigue_score += 0.8
    elif row["sleep_hours"] >= 8:
        fatigue_score -= 0.6

    if row["stress_level"] >= 5:
        fatigue_score += 1.2
    elif row["stress_level"] >= 4:
        fatigue_score += 0.8
    elif row["stress_level"] <= 2:
        fatigue_score -= 0.4

    # Cycle phase signals
    if row["cycle_phase"] == "menstrual":
        fatigue_score += 0.7
    elif row["cycle_phase"] == "luteal":
        fatigue_score += 0.5
    elif row["cycle_phase"] == "follicular":
        fatigue_score -= 0.4

    # Nutrition signals
    if row["protein_g"] < 15:
        fatigue_score += 0.5
    elif row["protein_g"] >= 35:
        fatigue_score -= 0.3

    if row["free_sugar_g"] > 45:
        fatigue_score += 0.4

    if row["fibre_g"] < 6:
        fatigue_score += 0.3

    if row["iron_mg"] < 5:
        fatigue_score += 0.6

    if row["folate_ug"] < 120:
        fatigue_score += 0.3

    if row["vitamin_c_mg"] < 20 and row["iron_mg"] < 7:
        fatigue_score += 0.2

    # Noise so data is not perfectly rule-based
    fatigue_score += np.random.normal(0, 0.45)

    return int(round(clamp(fatigue_score, 1, 5)))


def compute_mood_state(row, fatigue_level):
    scores = {
        "happy": 0.0,
        "sad": 0.0,
        "anxious": 0.0,
        "groggy": 0.0,
    }

    # Sleep
    if row["sleep_hours"] < 5.5:
        scores["groggy"] += 2.0
        scores["sad"] += 0.4
    elif row["sleep_hours"] >= 7.5:
        scores["happy"] += 1.0

    # Stress
    if row["stress_level"] >= 4:
        scores["anxious"] += 2.0
    elif row["stress_level"] <= 2:
        scores["happy"] += 0.8

    # Cycle phase
    if row["cycle_phase"] == "luteal":
        scores["anxious"] += 0.7
        scores["sad"] += 0.5
    elif row["cycle_phase"] == "menstrual":
        scores["sad"] += 0.7
        scores["groggy"] += 0.5
    elif row["cycle_phase"] == "follicular":
        scores["happy"] += 0.8

    # Nutrition
    if row["free_sugar_g"] > 45:
        scores["groggy"] += 0.6

    if row["protein_g"] < 15 or row["iron_mg"] < 5:
        scores["groggy"] += 0.5

    if row["fibre_g"] >= 10 and row["protein_g"] >= 25:
        scores["happy"] += 0.4

    if fatigue_level >= 4:
        scores["groggy"] += 0.6
        scores["sad"] += 0.3

    # Add randomness
    for mood in scores:
        scores[mood] += np.random.normal(0, 0.25)

    return max(scores, key=lambda mood: scores[mood])


def get_dominant_factor(row):
    factors = []

    if row["sleep_hours"] < 6:
        factors.append(("low_sleep", 2.0))
    if row["stress_level"] >= 4:
        factors.append(("high_stress", 1.8))
    if row["cycle_phase"] in ["menstrual", "luteal"]:
        factors.append((f"{row['cycle_phase']}_phase", 1.2))
    if row["protein_g"] < 15:
        factors.append(("low_protein", 0.9))
    if row["iron_mg"] < 5:
        factors.append(("low_iron", 1.1))
    if row["free_sugar_g"] > 45:
        factors.append(("high_free_sugar", 0.8))
    if row["fibre_g"] < 6:
        factors.append(("low_fibre", 0.6))
    if row["folate_ug"] < 120:
        factors.append(("low_folate", 0.5))

    if not factors:
        return "balanced_inputs"

    return sorted(factors, key=lambda x: x[1], reverse=True)[0][0]


def generate_row():
    row = {
        "cycle_phase": random.choice(CYCLE_PHASES),
        "sleep_hours": round(random.uniform(4, 9), 1),
        "stress_level": random.randint(1, 5),
    }

    row.update(generate_nutrition_values())

    fatigue_level = compute_fatigue_level(row)
    mood_state = compute_mood_state(row, fatigue_level)
    dominant_factor = get_dominant_factor(row)

    row["fatigue_level"] = fatigue_level
    row["mood_state"] = mood_state
    row["dominant_factor"] = dominant_factor

    return row


def generate_dataset(n_rows=1000, output_path="data/synthetic_health_data.csv"):
    rows = [generate_row() for _ in range(n_rows)]
    df = pd.DataFrame(rows)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    return df


if __name__ == "__main__":
    df = generate_dataset()
    print(df.head())
    print("\nSaved to data/synthetic_health_data.csv")
    print("\nFatigue distribution:")
    print(df["fatigue_level"].value_counts().sort_index())
    print("\nMood distribution:")
    print(df["mood_state"].value_counts())
