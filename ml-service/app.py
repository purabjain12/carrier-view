from pathlib import Path
from typing import List
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from simulation import project_path
from utils.preprocess import transform_single_input


ARTIFACT_DIR = Path("artifacts")
app = FastAPI(title="AI Career Simulator ML Service")


class SimulateRequest(BaseModel):
    educationLevel: str
    degreeStream: str
    skills: List[str] = Field(min_length=1)
    location: str
    interests: List[str] = []
    riskPreference: str
    yearsToSimulate: int = 10
    yearsExperience: int = 0


def load_artifacts():
    required_files = [
        "salary_model.joblib",
        "demand_model.joblib",
        "transition_model.joblib",
        "burnout_model.joblib",
        "preprocessor.joblib",
        "mlb_skills.joblib",
        "mlb_interests.joblib",
    ]
    for name in required_files:
        if not (ARTIFACT_DIR / name).exists():
            raise FileNotFoundError(
                f"Missing artifact {name}. Run python train.py in ml-service."
            )

    return {
        "salary_model": joblib.load(ARTIFACT_DIR / "salary_model.joblib"),
        "demand_model": joblib.load(ARTIFACT_DIR / "demand_model.joblib"),
        "transition_model": joblib.load(ARTIFACT_DIR / "transition_model.joblib"),
        "burnout_model": joblib.load(ARTIFACT_DIR / "burnout_model.joblib"),
        "preprocessor": joblib.load(ARTIFACT_DIR / "preprocessor.joblib"),
        "mlb_skills": joblib.load(ARTIFACT_DIR / "mlb_skills.joblib"),
        "mlb_interests": joblib.load(ARTIFACT_DIR / "mlb_interests.joblib"),
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "ml-service"}


@app.post("/simulate-career")
def simulate_career(payload: SimulateRequest):
    try:
        artifacts = load_artifacts()
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    X = transform_single_input(
        payload.model_dump(),
        artifacts["preprocessor"],
        artifacts["mlb_skills"],
        artifacts["mlb_interests"],
    )

    base_salary = float(artifacts["salary_model"].predict(X)[0])
    demand_probs = artifacts["demand_model"].predict_proba(X)[0]
    demand_score = float(np.max(demand_probs))
    transition_prob = float(artifacts["transition_model"].predict_proba(X)[0][1])
    burnout_prob = float(artifacts["burnout_model"].predict_proba(X)[0][1])

    candidate_paths = ["software_engineer", "data_scientist", "product_manager"]
    generated_paths = [
        project_path(
            path_name=path_name,
            base_salary=base_salary * (1 + i * 0.05),
            demand_score=demand_score - (i * 0.06),
            transition_prob=transition_prob - (i * 0.03),
            burnout_score=burnout_prob + (i * 0.04),
            years=payload.yearsToSimulate,
        )
        for i, path_name in enumerate(candidate_paths)
    ]

    return {
        "generatedPaths": generated_paths,
        "salaryMeta": {
            # Salary values are projected as annual INR figures.
            "currency": "INR",
            "period": "yearly",
        },
        "modelMetadata": {
            "salaryModelVersion": "rf_v1",
            "demandModelVersion": "rf_classifier_v1",
            "transitionModelVersion": "logreg_v1",
            "burnoutModelVersion": "hybrid_logreg_v1",
        },
    }
