"""
Job demand modeling for AI Career Simulator.

WHY this exists:
- Product needs simple explainable labels: Growing / Stable / Declining.
- We convert numeric demand proxy into discrete business labels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from feature_engineering import build_career_master
from data_preprocessing import normalize_job_title


ARTIFACT_DIR = Path("E:/Carrer View/ml-service/artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = ARTIFACT_DIR / "demand_classifier.joblib"
CAREER_MASTER_PATH = Path("E:/Carrer View/ml-service/data/career_master.csv")


def demand_label_from_score(score: float) -> str:
    if score >= 0.67:
        return "Growing"
    if score >= 0.40:
        return "Stable"
    return "Declining"


def build_demand_training_frame() -> pd.DataFrame:
    if CAREER_MASTER_PATH.exists():
        career_master = pd.read_csv(CAREER_MASTER_PATH)
    else:
        career_master = build_career_master()

    career_master["demand_label"] = career_master["demand_score"].map(demand_label_from_score)
    return career_master


def train_demand_model() -> Dict[str, float]:
    df = build_demand_training_frame()
    X = df[["demand_score", "postings_count", "skills_count", "avg_salary"]]
    y = df["demand_label"]

    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(X, y)
    accuracy = float(model.score(X, y))
    joblib.dump(model, MODEL_PATH)
    return {"training_accuracy": accuracy, "n_roles": float(len(df))}


def predict_job_demand(career_name: str) -> str:
    role = normalize_job_title(career_name)
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Demand model missing. Run demand_model.py first.")
    if not CAREER_MASTER_PATH.exists():
        raise FileNotFoundError("career_master missing. Run feature_engineering.py first.")

    model: DecisionTreeClassifier = joblib.load(MODEL_PATH)
    cm = pd.read_csv(CAREER_MASTER_PATH)
    row = cm[cm["career_name"] == role]
    if row.empty:
        # Fallback to median demand if role unseen.
        median_score = float(cm["demand_score"].median())
        return demand_label_from_score(median_score)

    X = row[["demand_score", "postings_count", "skills_count", "avg_salary"]]
    return str(model.predict(X)[0])


if __name__ == "__main__":
    report = train_demand_model()
    print("Demand model trained:", report)
