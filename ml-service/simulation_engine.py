"""
Career simulation engine for 5-year projections.

WHY this exists:
- We do not have trajectory data, so we model within-role growth transparently.
- Investors/professors can audit assumptions from explicit formulas.
"""

from __future__ import annotations

import math
from typing import Dict, List

import pandas as pd

from career_fit_score import compute_career_fit_score
from data_preprocessing import normalize_job_title
from demand_model import predict_job_demand
from train_salary_model import predict_salary


CAREER_MASTER_PATH = "E:/Carrer View/ml-service/data/career_master.csv"


DEMAND_ADJUSTMENTS = {
    "Growing": 0.03,
    "Stable": 0.01,
    "Declining": -0.01,
}


def _growth_curve(base_salary: float, annual_growth: float, years: int = 5) -> List[float]:
    values = []
    current = base_salary
    for _ in range(years):
        current = current * (1 + annual_growth)
        values.append(round(float(current), 2))
    return values


def _stability_score_from_demand(label: str) -> float:
    if label == "Growing":
        return 0.86
    if label == "Stable":
        return 0.70
    return 0.48


def _safe_float(value: float, fallback: float) -> float:
    """Return a finite float for API-safe responses."""
    try:
        cast = float(value)
        if math.isnan(cast) or math.isinf(cast):
            return float(fallback)
        return cast
    except (TypeError, ValueError):
        return float(fallback)


def _build_explanation(career_name: str, demand_label: str, top_skills: List[str]) -> str:
    """
    Keep explanation deterministic and always non-empty for frontend rendering.
    """
    skill_text = ", ".join(top_skills[:3]) if top_skills else "core domain skills"
    return (
        f"{career_name.title()} is currently marked as {demand_label.lower()} demand. "
        f"Focus on {skill_text} to improve long-term salary progression and role stability."
    )


def _sanitize_breakdown(raw_breakdown: Dict) -> Dict[str, Dict[str, object]]:
    """
    Normalize breakdown shape for API/frontend contract stability.
    Ensures one human-readable structure with consistent keys.
    """
    default_reasoning = {
        "skill_match": "Measures overlap between user skills and role-required top skills.",
        "salary_strength": "Reflects projected growth and salary position against p75 benchmark.",
        "demand": "Maps market demand label to a stable numeric score.",
        "stability": "Reuses the simulation stability estimate for reliability context.",
    }
    out = {}
    for key in ["skill_match", "salary_strength", "demand", "stability"]:
        block = raw_breakdown.get(key, {}) if isinstance(raw_breakdown, dict) else {}
        out[key] = {
            "component_score": _safe_float(block.get("component_score", 0.0), 0.0),
            "weight": _safe_float(block.get("weight", 0.0), 0.0),
            "contribution": _safe_float(block.get("contribution", 0.0), 0.0),
            "reasoning": str(block.get("reasoning") or default_reasoning[key]),
        }
    return out


def _apply_presentation_guardrails(best: List[float], avg: List[float], worst: List[float]) -> Dict[str, List[float]]:
    """
    Presentation guardrail:
    - best should not exceed 3x average
    - worst should not fall below 0.7x average
    This does not retrain or change core prediction logic; it only stabilizes displayed bands.
    """
    safe_avg = [_safe_float(v, 0.0) for v in avg]
    safe_best = [_safe_float(v, 0.0) for v in best]
    safe_worst = [_safe_float(v, 0.0) for v in worst]

    capped_best: List[float] = []
    capped_worst: List[float] = []
    for i, avg_val in enumerate(safe_avg):
        avg_floor = max(1.0, avg_val)
        best_cap = 3.0 * avg_floor
        worst_floor = 0.7 * avg_floor
        best_val = min(safe_best[i], best_cap)
        worst_val = max(safe_worst[i], worst_floor)
        capped_best.append(round(_safe_float(best_val, avg_floor), 2))
        capped_worst.append(round(_safe_float(worst_val, avg_floor), 2))

    return {
        "best": capped_best,
        "average": [round(_safe_float(v, 0.0), 2) for v in safe_avg],
        "worst": capped_worst,
    }


def simulate_career_outcome(career: str, skills: List[str], location: str) -> Dict:
    career_norm = normalize_job_title(career)
    if not career_norm:
        career_norm = "generalist"

    base_salary = _safe_float(predict_salary(career_norm, location, skills), 300000.0)
    demand_label = predict_job_demand(career_norm)
    if demand_label not in DEMAND_ADJUSTMENTS:
        demand_label = "Stable"

    cm = pd.read_csv(CAREER_MASTER_PATH)
    row = cm[cm["career_name"] == career_norm]
    if row.empty:
        p25 = _safe_float(base_salary * 0.80, base_salary)
        p75 = _safe_float(base_salary * 1.20, base_salary)
        top_skills = []
    else:
        p25 = _safe_float(row.iloc[0]["salary_p25"], base_salary * 0.80)
        p75 = _safe_float(row.iloc[0]["salary_p75"], base_salary * 1.20)
        top_skills_raw = row.iloc[0]["top_skills"]
        if pd.isna(top_skills_raw):
            top_skills = []
        else:
            top_skills = [
                s.strip()
                for s in str(top_skills_raw).split(",")
                if s.strip() and s.strip().lower() not in {"nan", "none", "null"}
            ]

    demand_adjust = DEMAND_ADJUSTMENTS[demand_label]
    base_growth = 0.08 + demand_adjust

    # Scenario interpretation:
    # - best uses optimistic percentile anchor + stronger growth
    # - average uses model prediction + base growth
    # - worst uses lower percentile anchor + reduced growth
    best = _growth_curve(max(base_salary, p75), base_growth + 0.02)
    avg = _growth_curve(base_salary, base_growth)
    worst = _growth_curve(min(base_salary, p25), max(0.01, base_growth - 0.03))

    # Contract hardening: never return empty/unsafe primary fields.
    if not top_skills:
        top_skills = [s for s in skills if s] or ["communication"]
    salary_projection = avg if avg else [round(base_salary, 2)] * 5
    salary_projection = [_safe_float(v, base_salary) for v in salary_projection]
    stability_score = _safe_float(_stability_score_from_demand(demand_label), 0.6)
    explanation = _build_explanation(career_norm, demand_label, top_skills)
    scenario_projection = _apply_presentation_guardrails(best, salary_projection, worst)

    fit_payload = compute_career_fit_score(
        user_skills=skills,
        career_top_skills=top_skills[:10],
        salary_projection=salary_projection,
        start_salary=base_salary,
        p75_salary=p75,
        demand_label=demand_label,
        stability_score=stability_score,
    )
    career_fit_breakdown = _sanitize_breakdown(
        fit_payload.get("score_breakdown", fit_payload.get("career_fit_breakdown", {}))
    )

    # Ordered, serialization-safe contract for API and frontend consumers.
    return {
        "career": career_norm.title(),
        "career_fit_score": _safe_float(fit_payload.get("career_fit_score", 0.0), 0.0),
        "career_fit_breakdown": career_fit_breakdown,
        "salary_projection": salary_projection,
        "salary_projection_scenarios": scenario_projection,
        "job_demand": demand_label,
        "stability_score": stability_score,
        "top_skills": top_skills[:10],
        "explanation": explanation,
    }


if __name__ == "__main__":
    sample = simulate_career_outcome(
        career="Data Analyst",
        skills=["sql", "excel", "python"],
        location="Bengaluru",
    )
    print(sample)
