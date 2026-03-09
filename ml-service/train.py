import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

from utils.preprocess import clean_dataframe, build_feature_matrix


DATA_DIR = Path("data")
ARTIFACT_DIR = Path("artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def load_merged_dataset():
    # MVP assumes a pre-joined dataset at training time.
    # In production, this should be a repeatable ETL pipeline that joins multiple tables.
    file_path = DATA_DIR / "career_training_data.csv"
    if not file_path.exists():
        raise FileNotFoundError(
            "Missing data/career_training_data.csv. Add a merged CSV before training."
        )
    return pd.read_csv(file_path)


def train_and_save():
    df = clean_dataframe(load_merged_dataset())
    X, preprocessor, mlb_skills, mlb_interests = build_feature_matrix(df)

    y_salary = df["salary"].values
    y_demand = df["demand_label"].fillna("stable").values
    y_transition = df["next_role_success"].fillna(0).astype(int).values
    y_burnout = df["burnout_label"].fillna(0).astype(int).values

    X_train, X_test, y_salary_train, y_salary_test = train_test_split(
        X, y_salary, test_size=0.2, random_state=42
    )
    salary_model = RandomForestRegressor(
        n_estimators=200, max_depth=10, random_state=42
    )
    salary_model.fit(X_train, y_salary_train)
    salary_pred = salary_model.predict(X_test)
    salary_mae = mean_absolute_error(y_salary_test, salary_pred)

    X_train, X_test, y_demand_train, y_demand_test = train_test_split(
        X, y_demand, test_size=0.2, random_state=42
    )
    demand_model = RandomForestClassifier(n_estimators=120, random_state=42)
    demand_model.fit(X_train, y_demand_train)
    demand_acc = accuracy_score(y_demand_test, demand_model.predict(X_test))

    transition_model = LogisticRegression(max_iter=500)
    transition_model.fit(X, y_transition)
    burnout_model = LogisticRegression(max_iter=500)
    burnout_model.fit(X, y_burnout)

    joblib.dump(salary_model, ARTIFACT_DIR / "salary_model.joblib")
    joblib.dump(demand_model, ARTIFACT_DIR / "demand_model.joblib")
    joblib.dump(transition_model, ARTIFACT_DIR / "transition_model.joblib")
    joblib.dump(burnout_model, ARTIFACT_DIR / "burnout_model.joblib")
    joblib.dump(preprocessor, ARTIFACT_DIR / "preprocessor.joblib")
    joblib.dump(mlb_skills, ARTIFACT_DIR / "mlb_skills.joblib")
    joblib.dump(mlb_interests, ARTIFACT_DIR / "mlb_interests.joblib")

    metrics = {
        "salary_mae": float(np.round(salary_mae, 2)),
        "demand_accuracy": float(np.round(demand_acc, 4)),
    }
    with open(ARTIFACT_DIR / "metrics.txt", "w", encoding="utf-8") as f:
        f.write(str(metrics))

    print("Training complete. Metrics:", metrics)


if __name__ == "__main__":
    train_and_save()
