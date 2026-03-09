"""
Career Fit Score module for product-facing confidence scoring.

WHY this exists:
- Product needs one simple, stable number users can trust in early demos.
- Score is fully explainable from existing simulation outputs (no new models/data).
"""

from __future__ import annotations

import math
from typing import Dict, List, Set


# Tunable in one place for safe product iteration.
CAREER_FIT_WEIGHTS = {
    "skill_match": 0.35,
    "salary_strength": 0.30,
    "demand": 0.20,
    "stability": 0.15,
}

DEMAND_SCORE_MAP = {
    "Growing": 1.0,
    "Stable": 0.6,
    "Declining": 0.3,
}


def _safe_float(value: float, fallback: float = 0.0) -> float:
    try:
        cast = float(value)
        if math.isnan(cast) or math.isinf(cast):
            return float(fallback)
        return cast
    except (TypeError, ValueError):
        return float(fallback)


def _clamp_01(value: float) -> float:
    safe = _safe_float(value, 0.0)
    if safe < 0.0:
        return 0.0
    if safe > 1.0:
        return 1.0
    return safe


def _normalize_skills(skills: List[str]) -> Set[str]:
    return {
        str(s).strip().lower()
        for s in (skills or [])
        if str(s).strip() and str(s).strip().lower() not in {"nan", "none", "null"}
    }


def _skill_match_score(user_skills: List[str], career_top_skills: List[str]) -> float:
    user = _normalize_skills(user_skills)
    career = _normalize_skills(career_top_skills)
    if not career:
        return 0.0
    overlap = len(user.intersection(career))
    return _clamp_01(overlap / len(career))


def _salary_strength_score(
    salary_projection: List[float], start_salary: float, p75_salary: float
) -> float:
    """
    Blend two deterministic signals:
    - 5-year growth slope proxy: relative growth over simulation horizon
    - percentile position: where predicted start salary sits vs p75 anchor
    """
    start = max(_safe_float(start_salary, 0.0), 1.0)
    projection = [_safe_float(v, start) for v in (salary_projection or [])]
    end = projection[-1] if projection else start

    growth_ratio = max(0.0, (end - start) / start)
    # 100% 5-year growth maps to 1.0; keeps scale intuitive.
    growth_norm = _clamp_01(growth_ratio / 1.0)

    p75 = max(_safe_float(p75_salary, start), 1.0)
    percentile_position = _clamp_01(start / p75)

    return _clamp_01((0.6 * growth_norm) + (0.4 * percentile_position))


def _demand_score(demand_label: str) -> float:
    return _clamp_01(DEMAND_SCORE_MAP.get(str(demand_label), DEMAND_SCORE_MAP["Stable"]))


def compute_career_fit_score(
    *,
    user_skills: List[str],
    career_top_skills: List[str],
    salary_projection: List[float],
    start_salary: float,
    p75_salary: float,
    demand_label: str,
    stability_score: float,
) -> Dict[str, object]:
    skill_match = _skill_match_score(user_skills, career_top_skills)
    salary_strength = _salary_strength_score(salary_projection, start_salary, p75_salary)
    demand = _demand_score(demand_label)
    stability = _clamp_01(stability_score)

    weighted_sum = (
        (skill_match * CAREER_FIT_WEIGHTS["skill_match"])
        + (salary_strength * CAREER_FIT_WEIGHTS["salary_strength"])
        + (demand * CAREER_FIT_WEIGHTS["demand"])
        + (stability * CAREER_FIT_WEIGHTS["stability"])
    )
    total_score = round(_clamp_01(weighted_sum) * 100.0, 2)

    # Detailed explainability payload for product UI copy and trust-building.
    score_breakdown = {
        "skill_match": {
            "component_score": round(skill_match, 4),
            "weight": CAREER_FIT_WEIGHTS["skill_match"],
            "contribution": round(skill_match * CAREER_FIT_WEIGHTS["skill_match"] * 100.0, 2),
            "reasoning": "Measures overlap between user skills and role-required top skills.",
        },
        "salary_strength": {
            "component_score": round(salary_strength, 4),
            "weight": CAREER_FIT_WEIGHTS["salary_strength"],
            "contribution": round(salary_strength * CAREER_FIT_WEIGHTS["salary_strength"] * 100.0, 2),
            "reasoning": "Combines projected 5-year growth with current position vs p75 salary benchmark.",
        },
        "demand": {
            "component_score": round(demand, 4),
            "weight": CAREER_FIT_WEIGHTS["demand"],
            "contribution": round(demand * CAREER_FIT_WEIGHTS["demand"] * 100.0, 2),
            "reasoning": "Maps market outlook label to a stable numeric score.",
        },
        "stability": {
            "component_score": round(stability, 4),
            "weight": CAREER_FIT_WEIGHTS["stability"],
            "contribution": round(stability * CAREER_FIT_WEIGHTS["stability"] * 100.0, 2),
            "reasoning": "Reuses career stability estimate from the simulation output.",
        },
    }

    return {
        "career_fit_score": total_score,
        # Compact component view requested by API integration contract.
        "career_fit_breakdown": {
            "skill_match": round(skill_match, 4),
            "salary_strength": round(salary_strength, 4),
            "demand": round(demand, 4),
            "stability": round(stability, 4),
        },
        "score_breakdown": score_breakdown,
    }
