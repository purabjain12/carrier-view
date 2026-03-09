"""
User adjustment layer for Career View personalization.

WHY this exists:
- Core models are intentionally stable and career-centric.
- This layer adds deterministic, explainable personalization without retraining.
- It runs after base simulation output and before API response.
"""

from __future__ import annotations

import math
from typing import Dict, List

from career_specializations import get_specialization_config, normalize_key


LOW_RISK_SPREAD_FACTOR = 0.70
MEDIUM_RISK_SPREAD_FACTOR = 1.00
HIGH_RISK_SPREAD_FACTOR = 1.30
# If user skill-match is weak for a career, we dampen growth for that career only.
LOW_SKILL_MATCH_GROWTH_PENALTY = 0.90
# "coding" interest can amplify DS growth as a targeted career-specific boost.
CODING_DS_GROWTH_BONUS = 1.05


def _safe_float(value: object, fallback: float = 0.0) -> float:
    try:
        cast = float(value)
        if math.isnan(cast) or math.isinf(cast):
            return float(fallback)
        return cast
    except (TypeError, ValueError):
        return float(fallback)


def _normalize_tokens(values: List[str]) -> List[str]:
    return [str(v).strip().lower() for v in (values or []) if str(v).strip()]


def _extract_target_years(user_profile: Dict) -> int:
    raw = (
        user_profile.get("yearsToSimulate")
        or user_profile.get("years_to_simulate")
        or user_profile.get("years")
        or 5
    )
    years = int(_safe_float(raw, 5))
    return max(1, min(10, years))


def _extract_degree_stream(user_profile: Dict) -> str:
    return str(
        user_profile.get("degreeStream")
        or user_profile.get("degree_stream")
        or user_profile.get("stream")
        or ""
    ).strip().lower()


def _career_key(career_name: str) -> str:
    return normalize_key(career_name)


def _career_domain_keywords(career_name: str) -> List[str]:
    c = _career_key(career_name)
    if "data" in c or "analyst" in c or "scientist" in c or "ai" in c:
        return ["data", "analytics", "computer", "statistics", "math", "it"]
    if "software" in c or "developer" in c or "engineer" in c:
        return ["computer", "software", "it", "engineering", "tech"]
    if "product" in c or "manager" in c:
        return ["product", "business", "management", "mba", "commerce", "marketing"]
    return ["general", "business", "technology"]


def _degree_salary_multiplier(career_name: str, degree_stream: str) -> float:
    """
    Career-aware degree effect:
    - If degree mentions CS/Computer Science, differentiate by career family.
    - Else use existing domain-alignment fallback.
    """
    if not degree_stream:
        return 0.95
    career = _career_key(career_name)
    ds = degree_stream.lower()

    if "cs" in ds or "computer science" in ds or "computer" in ds:
        degree_map = {
            "software_engineer": 1.08,
            "data_scientist": 1.06,
            "data_analyst": 1.04,
            "product_manager": 1.02,
        }
        if career in degree_map:
            return degree_map[career]

    keywords = _career_domain_keywords(career_name)
    aligned = any(keyword in degree_stream for keyword in keywords)
    return 1.05 if aligned else 0.95


def _interests_align_with_career(career_name: str, interests: List[str]) -> bool:
    if not interests:
        return False
    interest_tokens = set(" ".join(_normalize_tokens(interests)).split())
    domain_tokens = set(_career_domain_keywords(career_name))
    return len(interest_tokens.intersection(domain_tokens)) > 0


def _extract_skill_match_score(base_output: Dict) -> float:
    breakdown = base_output.get("career_fit_breakdown", {})
    if isinstance(breakdown, dict):
        skill_match = breakdown.get("skill_match")
        if isinstance(skill_match, dict):
            return _safe_float(skill_match.get("component_score"), 0.0)
        return _safe_float(skill_match, 0.0)
    return 0.0


def _apply_growth_modifier(series: List[float], growth_factor: float) -> List[float]:
    """
    Adjust growth trajectory while preserving first-year anchor.
    Used for career-specific penalties/bonuses without changing base model prediction.
    """
    if not series:
        return []
    first = _safe_float(series[0], 0.0)
    out = [round(first, 2)]
    prev_base = first
    current = first
    for idx in range(1, len(series)):
        base_now = _safe_float(series[idx], prev_base)
        denom = max(prev_base, 1.0)
        base_growth = (base_now - prev_base) / denom
        adjusted_growth = base_growth * growth_factor
        current = current * (1 + adjusted_growth)
        out.append(round(_safe_float(current, 0.0), 2))
        prev_base = base_now
    return out


def _resample_projection(series: List[float], target_years: int) -> List[float]:
    clean = [_safe_float(v, 0.0) for v in (series or [])]
    if not clean:
        return [0.0] * target_years
    if len(clean) == target_years:
        return [round(v, 2) for v in clean]
    if len(clean) > target_years:
        return [round(v, 2) for v in clean[:target_years]]

    # Extend deterministically using average observed yearly growth.
    growth_rates = []
    for prev, curr in zip(clean[:-1], clean[1:]):
        denom = max(prev, 1.0)
        growth_rates.append((curr - prev) / denom)
    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.05

    out = clean[:]
    while len(out) < target_years:
        out.append(out[-1] * (1 + avg_growth))
    return [round(_safe_float(v, 0.0), 2) for v in out]


def _apply_risk_spread(
    best: List[float],
    avg: List[float],
    worst: List[float],
    risk_preference: str,
    specialization_risk_modifier: float = 1.0,
):
    risk = str(risk_preference or "medium").strip().lower()
    if risk == "low":
        factor = LOW_RISK_SPREAD_FACTOR
    elif risk == "high":
        factor = HIGH_RISK_SPREAD_FACTOR
    else:
        factor = MEDIUM_RISK_SPREAD_FACTOR
    # Specialization-level risk modifier lets roles differ within same family.
    factor = factor * max(0.75, min(1.30, _safe_float(specialization_risk_modifier, 1.0)))

    adj_best: List[float] = []
    adj_worst: List[float] = []
    for b, a, w in zip(best, avg, worst):
        b = _safe_float(b, a)
        a = _safe_float(a, 0.0)
        w = _safe_float(w, a)

        # Spread around average based on risk profile.
        best_delta = max(0.0, b - a) * factor
        worst_delta = max(0.0, a - w) * factor
        new_best = a + best_delta
        new_worst = a - worst_delta

        # Keep same presentation guardrails as core output contract.
        guard_best_cap = 3.0 * max(a, 1.0)
        guard_worst_floor = 0.7 * max(a, 1.0)
        adj_best.append(round(min(new_best, guard_best_cap), 2))
        adj_worst.append(round(max(new_worst, guard_worst_floor), 2))

    return adj_best, adj_worst


def apply_user_adjustments(base_output: Dict, user_profile: Dict) -> Dict:
    """
    Apply deterministic personalization to a single-career simulation output.
    """
    adjusted = dict(base_output or {})
    career_name = str(adjusted.get("career", "career"))

    years = _extract_target_years(user_profile)
    degree_stream = _extract_degree_stream(user_profile)
    interests = user_profile.get("interests") or []
    risk_preference = user_profile.get("riskPreference") or user_profile.get("risk_preference") or "medium"
    interest_tokens = set(_normalize_tokens(interests))
    career_key = _career_key(career_name)
    specialization_raw = str(user_profile.get("specialization", "")).strip()
    specialization_key = _career_key(specialization_raw)
    specialization_cfg = get_specialization_config(specialization_key, career_key)

    salary_multiplier = _degree_salary_multiplier(career_name, degree_stream)
    skill_match_score = _extract_skill_match_score(adjusted)

    avg = _resample_projection(adjusted.get("salary_projection", []), years)
    avg = [round(_safe_float(v, 0.0) * salary_multiplier, 2) for v in avg]

    scenarios = adjusted.get("salary_projection_scenarios", {})
    best = _resample_projection(scenarios.get("best", avg), years)
    worst = _resample_projection(scenarios.get("worst", avg), years)
    best = [round(_safe_float(v, 0.0) * salary_multiplier, 2) for v in best]
    worst = [round(_safe_float(v, 0.0) * salary_multiplier, 2) for v in worst]

    explanation_reasons: List[str] = []
    if salary_multiplier > 1.0:
        explanation_reasons.append(
            "your degree background maps strongly to this career, lifting salary potential"
        )
    else:
        explanation_reasons.append(
            "your degree is less directly aligned with this career, slightly reducing salary advantage"
        )

    # Interest-specific career modifiers:
    # - coding -> software_engineer stability +0.05
    # - coding -> data_scientist growth +5%
    # - coding -> product_manager burnout pressure +5 points (reported in explanation)
    coding_interest = "coding" in interest_tokens
    burnout_delta_points = 0
    if coding_interest and career_key == "data_scientist":
        avg = _apply_growth_modifier(avg, CODING_DS_GROWTH_BONUS)
        best = _apply_growth_modifier(best, CODING_DS_GROWTH_BONUS)
        worst = _apply_growth_modifier(worst, CODING_DS_GROWTH_BONUS)
        explanation_reasons.append(
            "your coding interest boosts long-term growth in this technical path"
        )
    if skill_match_score < 0.5:
        # Career-specific skill gap penalty only when skill fit is weak.
        avg = _apply_growth_modifier(avg, LOW_SKILL_MATCH_GROWTH_PENALTY)
        best = _apply_growth_modifier(best, LOW_SKILL_MATCH_GROWTH_PENALTY)
        worst = _apply_growth_modifier(worst, LOW_SKILL_MATCH_GROWTH_PENALTY)
        explanation_reasons.append(
            "current skill overlap is low, so growth is moderated until the gap is closed"
        )

    specialization_risk_modifier = 1.0
    if specialization_cfg:
        # Specialization modifier tunes role-specific direction, not base model outputs.
        spec_growth_modifier = _safe_float(specialization_cfg.get("growth_modifier"), 1.0)
        spec_stability_modifier = _safe_float(specialization_cfg.get("stability_modifier"), 0.0)
        specialization_risk_modifier = _safe_float(
            specialization_cfg.get("risk_modifier"), 1.0
        )

        avg = _apply_growth_modifier(avg, spec_growth_modifier)
        best = _apply_growth_modifier(best, spec_growth_modifier)
        worst = _apply_growth_modifier(worst, spec_growth_modifier)

        emphasis = ", ".join(specialization_cfg.get("primary_skill_emphasis", [])[:3])
        explanation_reasons.append(
            f"{specialization_raw.replace('_', ' ').title()} is modeled as a specialized "
            f"{career_name.title()} track with emphasis on {emphasis or 'core specialization skills'}"
        )
        if spec_growth_modifier > 1.0:
            explanation_reasons.append("this specialization has higher upside salary acceleration")
        elif spec_growth_modifier < 1.0:
            explanation_reasons.append("this specialization has steadier but slower salary acceleration")
    else:
        spec_stability_modifier = 0.0

    best, worst = _apply_risk_spread(
        best,
        avg,
        worst,
        str(risk_preference),
        specialization_risk_modifier=specialization_risk_modifier,
    )

    adjusted["salary_projection"] = avg
    adjusted["salary_projection_scenarios"] = {
        "best": best,
        "average": avg,
        "worst": worst,
    }

    # Interests alignment rule: +5 stability points and -5 burnout points.
    # Stability is normalized 0..1, so +5 points maps to +0.05.
    stability = _safe_float(adjusted.get("stability_score", 0.0), 0.0)
    if coding_interest and career_key == "software_engineer":
        stability = min(1.0, stability + 0.05)
        explanation_reasons.append(
            "your coding interest improves stability for software engineering roles"
        )
    elif _interests_align_with_career(career_name, interests):
        stability = min(1.0, stability + 0.05)
        explanation_reasons.append(
            "your broader interests align with this career, improving long-term stability"
        )
    if coding_interest and career_key == "product_manager":
        burnout_delta_points = 5
        explanation_reasons.append(
            "coding-heavy preference may increase burnout risk in people-centric product roles"
        )

    # Apply specialization stability direction after broader user-interest rules.
    stability = min(1.0, max(0.0, stability + spec_stability_modifier))
    adjusted["stability_score"] = round(stability, 4)

    # Burnout is not exposed as a top-level field in the current contract,
    # so we communicate any burnout delta in plain language without changing schema.
    explanation = str(adjusted.get("explanation", "")).strip()
    if not explanation_reasons:
        explanation_reasons.append(
            "personalization is neutral for this career based on your current profile"
        )
    burnout_phrase = ""
    if burnout_delta_points > 0:
        burnout_phrase = f"; estimated burnout pressure may be higher by about {burnout_delta_points} points"
    explanation_suffix = " Personalization: " + "; ".join(explanation_reasons) + burnout_phrase + "."
    adjusted["explanation"] = (explanation + explanation_suffix).strip()

    return adjusted
