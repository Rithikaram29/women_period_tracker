import os
from pathlib import Path
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "synthetic_health_data.csv"
MODEL_DIR = Path(__file__).resolve().parent.parent / "prediction_models"

TARGETS = ["fatigue_level", "mood_state"]
DROP_COLS = ["dominant_factor"]

CATEGORICAL_FEATURES = ["cycle_phase"]
NUMERIC_FEATURES = [
    "sleep_hours", "stress_level", "carbs_g", "protein_g", "fats_g",
    "free_sugar_g", "fibre_g", "sodium_mg", "calcium_mg", "iron_mg",
    "vitamin_c_mg", "folate_ug",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def build_model():
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", model),
        ]
    )

    return pipeline


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    X = df[FEATURES]
    y_fatigue = df["fatigue_level"]
    y_mood = df["mood_state"]

    X_train, X_test, y_fatigue_train, y_fatigue_test, y_mood_train, y_mood_test = train_test_split(
        X,
        y_fatigue,
        y_mood,
        test_size=0.2,
        random_state=42,
        stratify=y_mood,
    )

    fatigue_model = build_model()
    mood_model = build_model()

    fatigue_model.fit(X_train, y_fatigue_train)
    mood_model.fit(X_train, y_mood_train)

    fatigue_preds = fatigue_model.predict(X_test)
    mood_preds = mood_model.predict(X_test)

    print("\n=== Fatigue Model Results ===")
    print("Accuracy:", accuracy_score(y_fatigue_test, fatigue_preds))
    print(classification_report(y_fatigue_test, fatigue_preds))

    print("\n=== Mood Model Results ===")
    print("Accuracy:", accuracy_score(y_mood_test, mood_preds))
    print(classification_report(y_mood_test, mood_preds))

    joblib.dump(fatigue_model, f"{MODEL_DIR}/fatigue_model.pkl")
    joblib.dump(mood_model, f"{MODEL_DIR}/mood_model.pkl")

    print("\nModels saved:")
    print(f"{MODEL_DIR}/fatigue_model.pkl")
    print(f"{MODEL_DIR}/mood_model.pkl")


def predict_fatigue_and_mood(features: dict) -> dict:
    fatigue_model = joblib.load(MODEL_DIR / "fatigue_model.pkl")
    mood_model = joblib.load(MODEL_DIR / "mood_model.pkl")
    input_df = pd.DataFrame([features])[FEATURES]
    return {
        "fatigue_level": str(fatigue_model.predict(input_df)[0]),
        "mood_state": str(mood_model.predict(input_df)[0]),
    }


if __name__ == "__main__":
    train()