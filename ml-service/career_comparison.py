"""
Career comparison module for product-facing reports.

WHY this exists:
- Users need side-by-side career choices for onboarding and paid reports.
- We reuse stable simulation outputs to avoid retraining or architecture changes.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from simulation_engine import simulate_career_outcome
from user_adjustment import apply_user_adjustments


DEMAND_RANK = {
    "Growing": 3,
    "Stable": 2,
    "Declining": 1,
}


def _safe_float(value: object, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _year5_salary(salary_projection: List[float]) -> float:
    if not salary_projection:
        return 0.0
    return _safe_float(salary_projection[-1], 0.0)


def _salary_growth_ratio(salary_projection: List[float]) -> float:
    if not salary_projection:
        return 0.0
    start = max(_safe_float(salary_projection[0], 0.0), 1.0)
    end = _safe_float(salary_projection[-1], start)
    return max(0.0, (end - start) / start)


def _build_strengths(item: Dict) -> List[str]:
    strengths: List[str] = []

    fit = _safe_float(item.get("career_fit_score"), 0.0)
    demand = str(item.get("job_demand", "Stable"))
    stability = _safe_float(item.get("stability_score"), 0.0)
    year5_salary = _year5_salary(item.get("salary_projection", []))

    if fit >= 70:
        strengths.append("High overall fit with your profile.")
    elif fit >= 55:
        strengths.append("Good alignment with your skills and goals.")
    else:
        strengths.append("Moderate fit with room to improve through targeted upskilling.")

    if demand == "Growing":
        strengths.append("Strong market demand outlook.")
    elif demand == "Stable":
        strengths.append("Steady market demand with predictable opportunities.")
    else:
        strengths.append("Still viable, but demand is more competitive.")

    if stability >= 0.75:
        strengths.append("High career stability over the next few years.")
    elif stability >= 0.6:
        strengths.append("Balanced stability for medium-term planning.")
    else:
        strengths.append("Can be pursued with a focused skill-building plan.")

    if year5_salary > 0:
        strengths.append(f"Estimated year-5 salary reaches about {round(year5_salary, 2)}.")

    return strengths[:4]


def _build_tradeoffs(item: Dict) -> List[str]:
    tradeoffs: List[str] = []

    fit = _safe_float(item.get("career_fit_score"), 0.0)
    demand = str(item.get("job_demand", "Stable"))
    stability = _safe_float(item.get("stability_score"), 0.0)
    growth_ratio = _salary_growth_ratio(item.get("salary_projection", []))

    if fit < 55:
        tradeoffs.append("Needs stronger skill alignment to maximize outcomes.")
    if demand == "Declining":
        tradeoffs.append("Lower demand means tougher competition for roles.")
    if stability < 0.6:
        tradeoffs.append("Lower stability may require proactive upskilling.")
    if growth_ratio < 0.20:
        tradeoffs.append("Salary growth is steady but not aggressive.")

    if not tradeoffs:
        tradeoffs.append("No major tradeoff, but continuous skill updates remain important.")

    return tradeoffs[:4]


def _recommendation_sort_key(row: Dict) -> Tuple[float, int, float]:
    """
    Deterministic ranking logic:
    1) Higher career_fit_score wins
    2) Tie-break with better demand outlook
    3) Tie-break with higher salary growth ratio
    """
    fit_score = _safe_float(row.get("career_fit_score"), 0.0)
    demand_rank = DEMAND_RANK.get(str(row.get("job_demand", "Stable")), 2)
    growth_ratio = _salary_growth_ratio(row.get("salary_projection", []))
    return (fit_score, demand_rank, growth_ratio)


def compare_careers(user_profile: Dict, career_list: List[str]) -> Dict:
    if len(career_list) < 2 or len(career_list) > 3:
        raise ValueError("career_list must contain 2 or 3 careers.")

    required_keys = {"skills", "location"}
    missing = [k for k in required_keys if k not in user_profile]
    if missing:
        raise ValueError(f"user_profile missing required keys: {missing}")

    simulated_rows: List[Dict] = []
    for career in career_list:
        base_result = simulate_career_outcome(
            career=career,
            skills=user_profile.get("skills", []),
            location=user_profile.get("location", ""),
        )
        # Keep comparison consistent with single-career pipeline:
        # every career must pass through the same user personalization layer.
        adjusted_result = apply_user_adjustments(
            base_output=base_result,
            user_profile=user_profile,
        )
        simulated_rows.append(adjusted_result)

    comparison_rows: List[Dict] = []
    for row in simulated_rows:
        year5 = _year5_salary(row.get("salary_projection", []))
        comparison_item = {
            "career": row.get("career", ""),
            "career_fit_score": _safe_float(row.get("career_fit_score"), 0.0),
            "avg_salary_year_5": round(year5, 2),
            "job_demand": row.get("job_demand", "Stable"),
            # pulled from adjusted output
            "stability_score": _safe_float(row.get("stability_score"), 0.0),
            # short user-facing explanation snippet from adjusted output
            "explanation_snippet": str(row.get("explanation", "")).strip(),
            "strengths": _build_strengths(row),
            "tradeoffs": _build_tradeoffs(row),
            # internal fields for deterministic recommendation tie-breaks
            "_salary_projection": row.get("salary_projection", []),
        }
        if "burnout_risk" in row:
            # included only when upstream output provides it
            comparison_item["burnout_risk"] = _safe_float(row.get("burnout_risk"), 0.0)
        comparison_rows.append(comparison_item)

    ranked = sorted(comparison_rows, key=_recommendation_sort_key, reverse=True)
    recommended = ranked[0]

    runner_up = ranked[1]
    recommendation_reason = (
        f"{recommended['career']} is recommended because it has the strongest overall fit score "
        f"({recommended['career_fit_score']}) among compared options. "
        f"It also has a {recommended['job_demand'].lower()} demand outlook and "
        f"a stronger personalized 5-year salary path versus {runner_up['career']}."
    )

    # Remove internal-only fields before returning API payload.
    for row in comparison_rows:
        row.pop("_salary_projection", None)

    return {
        "careers_compared": [str(c) for c in career_list],
        "comparison": comparison_rows,
        "recommended_career": recommended["career"],
        "recommendation_reason": recommendation_reason,
    }


if __name__ == "__main__":
    sample_user_profile = {
        "skills": ["sql", "python", "excel", "tableau"],
        "location": "Bengaluru",
    }
    sample_career_list = ["Data Analyst", "Product Manager", "Data Scientist"]
    print(compare_careers(sample_user_profile, sample_career_list))
