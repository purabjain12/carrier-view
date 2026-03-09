"""
Train explainable salary prediction model.

Model choice:
- RandomForestRegressor (still interpretable enough with feature importance)
- Handles non-linear interactions between career/location/skill overlap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from data_preprocessing import run_preprocessing, normalize_job_title, normalize_text, parse_skill_tokens
from feature_engineering import build_career_master


ARTIFACT_DIR = Path("E:/Carrer View/ml-service/artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = ARTIFACT_DIR / "salary_regressor.joblib"
SKILL_MAP_PATH = ARTIFACT_DIR / "role_skill_map.joblib"


def _get_primary_skill(skill_list: List[str]) -> str:
    return skill_list[0] if skill_list else "unknown"


def create_salary_training_frame() -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    data = run_preprocessing()
    career_master = build_career_master()

    # Role -> top skills for overlap/similarity features at inference time.
    role_skill_map: Dict[str, List[str]] = {
        row["career_name"]: [s for s in str(row["top_skills"]).split(",") if s]
        for _, row in career_master.iterrows()
    }

    india_rows = data.india_market[["career_name", "location_clean", "salary_inr_annual"]].copy()
    india_rows["source"] = "india_market"
    india_rows.rename(columns={"salary_inr_annual": "target_salary"}, inplace=True)

    ds_rows = data.ds_salary[["career_name", "location_clean", "salary_usd"]].copy()
    ds_rows["source"] = "ds_salary"
    ds_rows["target_salary"] = ds_rows["salary_usd"] * 83.0
    ds_rows = ds_rows.drop(columns=["salary_usd"])

    train_df = pd.concat([india_rows, ds_rows], ignore_index=True)
    train_df = train_df.dropna(subset=["target_salary"])
    train_df = train_df[train_df["career_name"] != ""]

    # Add simple skill proxy per role so salary can react to role-skill richness.
    train_df["primary_skill"] = train_df["career_name"].map(
        lambda role: _get_primary_skill(role_skill_map.get(role, []))
    )
    train_df["role_skill_count"] = train_df["career_name"].map(
        lambda role: len(role_skill_map.get(role, []))
    )
    return train_df, role_skill_map


def train_salary_model() -> Dict[str, float]:
    train_df, role_skill_map = create_salary_training_frame()

    X = train_df[["career_name", "location_clean", "source", "primary_skill", "role_skill_count"]]
    y = train_df["target_salary"].values

    categorical_cols = ["career_name", "location_clean", "source", "primary_skill"]
    numeric_cols = ["role_skill_count"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    model = RandomForestRegressor(n_estimators=250, max_depth=16, random_state=42)
    pipeline = Pipeline(steps=[("prep", preprocessor), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    metrics = {
        "mae": float(mean_absolute_error(y_test, preds)),
        "r2": float(r2_score(y_test, preds)),
        "n_samples": float(len(train_df)),
    }

    joblib.dump(pipeline, MODEL_PATH)
    joblib.dump(role_skill_map, SKILL_MAP_PATH)
    return metrics


def predict_salary(career: str, location: str, skills: List[str]) -> float:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Salary model not found. Run train_salary_model.py first.")

    model: Pipeline = joblib.load(MODEL_PATH)
    role_skill_map: Dict[str, List[str]] = joblib.load(SKILL_MAP_PATH)

    career_norm = normalize_job_title(career)
    location_norm = normalize_text(location)
    skills_norm = parse_skill_tokens(",".join(skills))

    top_role_skills = set(role_skill_map.get(career_norm, []))
    overlap = [s for s in skills_norm if s in top_role_skills]
    primary_skill = overlap[0] if overlap else _get_primary_skill(role_skill_map.get(career_norm, []))

    X_pred = pd.DataFrame(
        [
            {
                "career_name": career_norm,
                "location_clean": location_norm,
                "source": "india_market",  # Use market anchor for local projection.
                "primary_skill": primary_skill,
                "role_skill_count": len(top_role_skills),
            }
        ]
    )
    return float(model.predict(X_pred)[0])


if __name__ == "__main__":
    report = train_salary_model()
    print("Salary model trained:", report)
