"""
Career View Service - AI Career Navigator backend entry point.

What this service does:
- Provides one public function, `run_career_view(user_profile, careers=None, career_stage=None)`.
- If career_stage is after_10th, after_12th, or college_student: runs navigation layer first.
- If career_stage is working_professional or career is determined: runs existing simulation.
- Routes to existing stable modules:
  - navigation via `navigation.career_navigation_engine`
  - single-career simulation via `simulation_engine`
  - multi-career comparison via `career_comparison`
- Normalizes outputs into JSON-safe, frontend-ready dictionaries.

Expected input format:
- user_profile: dict
  - required for simulation: `skills` (list[str]), `location` (str)
  - for navigation stages: `interests` (list[str]) optional, `skills` optional for early stages
  - for single-career mode (careers=None): must include `career` (str) when not using navigation
  - optional: `career_stage` (str) - after_10th, after_12th, college_student, working_professional
- careers: optional list[str]
  - if provided, must contain 2 or 3 careers
- career_stage: optional str
  - after_10th | after_12th | college_student | working_professional

Example usage:
    single = run_career_view(
        user_profile={
            "career": "Data Analyst",
            "skills": ["sql", "python", "excel"],
            "location": "Bengaluru",
        }
    )

    comparison = run_career_view(
        user_profile={
            "skills": ["sql", "python", "excel"],
            "location": "Bengaluru",
        },
        careers=["Data Analyst", "Product Manager", "Data Scientist"],
    )

What NOT to modify here:
- Do not add new prediction logic or model training.
- Do not change output contracts returned by core modules.
- Keep this module as routing/validation/safety boundary only.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from career_comparison import compare_careers
from simulation_engine import simulate_career_outcome

try:
    from navigation.career_navigation_engine import navigate_career
    from navigation.branch_recommender import load_branch_career_dataset
    _NAV_AVAILABLE = True
except ImportError:
    _NAV_AVAILABLE = False
from supported_careers import (
    STANDARD_DISCLAIMER,
    SUPPORTED_CAREER_FAMILIES,
    confidence_level_for,
    is_specialization_supported_for_family,
    resolve_career_family,
    resolve_specialization,
)
from user_adjustment import apply_user_adjustments


def _to_json_safe(value: Any) -> Any:
    """Recursively convert output to JSON-safe primitives."""
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return float(value)
    if value is None:
        return ""
    return value


def _validate_user_profile(user_profile: Any, career_stage: Optional[str] = None) -> Optional[str]:
    if not isinstance(user_profile, dict):
        return "user_profile must be a dictionary."
    stage = (career_stage or str(user_profile.get("career_stage", "")).strip() or "").lower().replace(" ", "_")
    nav_stages = {"after_10th", "after_12th", "college_student"}
    if stage in nav_stages:
        # Navigation stages: relax validation; interests helpful, skills optional
        if user_profile.get("interests") is not None and not isinstance(user_profile.get("interests"), list):
            return "Field 'interests' must be a list of strings."
        if user_profile.get("skills") is not None and not isinstance(user_profile.get("skills"), list):
            return "Field 'skills' must be a list of strings."
        return None
    # Simulation mode: require skills and location
    if "skills" not in user_profile:
        return "Missing required field: skills."
    if "location" not in user_profile:
        return "Missing required field: location."
    if not isinstance(user_profile.get("skills"), list):
        return "Field 'skills' must be a list of strings."
    if not isinstance(user_profile.get("location"), str) or not user_profile.get("location", "").strip():
        return "Field 'location' must be a non-empty string."
    return None


def _error_response(message: str) -> Dict[str, Any]:
    # User-facing, no stack traces.
    return {
        "ok": False,
        "error": {
            "message": message,
            "code": "INVALID_REQUEST",
        },
    }


def _unsupported_role_error() -> Dict[str, Any]:
    return _error_response(
        "This role is not supported yet. Career View currently focuses on CS careers."
    )


def _unsupported_specialization_error() -> Dict[str, Any]:
    return _error_response(
        "This specialization is not supported yet for the selected career family."
    )


def _aggregate_confidence(levels: List[str]) -> str:
    rank = {"Low": 1, "Medium": 2, "High": 3}
    if not levels:
        return "Low"
    min_level = min(levels, key=lambda lvl: rank.get(lvl, 1))
    return min_level


def _branch_to_career_family(branch: str) -> Optional[str]:
    """Map engineering branch to supported career_family for simulation."""
    if not _NAV_AVAILABLE:
        return None
    try:
        df = load_branch_career_dataset()
        branch_norm = str(branch or "").strip().lower().replace(" ", "_")
        row = df[df["branch"].fillna("").str.strip().str.lower() == branch_norm]
        if row.empty:
            return None
        cf = str(row.iloc[0].get("career_family", "")).strip().lower()
        if cf and cf in {"software_engineer", "data_analyst", "data_scientist", "product_manager"}:
            return cf
        return None
    except Exception:
        return None


def run_career_view(
    user_profile: Dict[str, Any],
    careers: Optional[List[str]] = None,
    career_stage: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Public entry point for AI Career Navigator backend.

    Routing:
    - career_stage in (after_10th, after_12th, college_student): run navigation first
    - career_stage == working_professional or career determined: run simulation
    - careers is None  -> single-career simulation
    - careers is list  -> career comparison (2-3 careers)
    """
    stage = (career_stage or str(user_profile.get("career_stage", "")).strip() or "").lower().replace(" ", "_")
    profile_error = _validate_user_profile(user_profile, career_stage)
    if profile_error:
        return _error_response(profile_error)

    try:
        nav_stages = {"after_10th", "after_12th", "college_student"}
        if stage in nav_stages and _NAV_AVAILABLE:
            nav_result = navigate_career(stage=stage, user_profile=user_profile)
            # If college_student and we have branch -> career mapping and user has skills+location, run simulation
            if (
                stage == "college_student"
                and nav_result.get("recommended_branches")
                and user_profile.get("skills")
                and user_profile.get("location", "").strip()
            ):
                top_branch = nav_result["recommended_branches"][0]
                career_family = _branch_to_career_family(top_branch)
                if career_family:
                    career_display = SUPPORTED_CAREER_FAMILIES.get(career_family) or career_family.replace("_", " ").title()
                    sim_result = simulate_career_outcome(
                        career=career_display,
                        skills=user_profile.get("skills", []),
                        location=user_profile.get("location", ""),
                    )
                    adjusted = apply_user_adjustments(
                        base_output=sim_result,
                        user_profile=dict(user_profile, career_family=career_family),
                    )
                    nav_result["simulation"] = _to_json_safe(adjusted)
                    nav_result["simulation"]["disclaimer"] = STANDARD_DISCLAIMER
                    nav_result["simulation"]["confidence_level"] = confidence_level_for(career_family, None)
            return _to_json_safe(nav_result)

        if careers is None:
            # Backward compatible:
            # - preferred new key: career_family
            # - legacy key: career
            career_raw = str(
                user_profile.get("career")
                or user_profile.get("career_family")
                or ""
            ).strip()
            if not career_raw:
                return _error_response(
                    "Single-career mode requires user_profile['career'] or user_profile['career_family']."
                )
            career_family = resolve_career_family(career_raw)
            if not career_family:
                return _unsupported_role_error()

            specialization_raw = str(user_profile.get("specialization", "")).strip()
            specialization = None
            if specialization_raw:
                specialization = resolve_specialization(specialization_raw)
                if not specialization:
                    return _unsupported_specialization_error()
                if not is_specialization_supported_for_family(specialization, career_family):
                    return _unsupported_specialization_error()

            result = simulate_career_outcome(
                career=career_family,
                skills=user_profile.get("skills", []),
                location=user_profile.get("location", ""),
            )
            # Personalization layer runs after core simulation without touching model logic.
            adjusted_profile = dict(user_profile)
            if specialization:
                adjusted_profile["specialization"] = specialization
            result = apply_user_adjustments(base_output=result, user_profile=adjusted_profile)
            result["disclaimer"] = STANDARD_DISCLAIMER
            result["confidence_level"] = confidence_level_for(career_family, specialization)
            return _to_json_safe(result)

        if not isinstance(careers, list):
            return _error_response("careers must be a list of 2 or 3 career names.")
        if len(careers) < 2 or len(careers) > 3:
            return _error_response("careers must contain exactly 2 or 3 items.")
        if any(not isinstance(c, str) or not c.strip() for c in careers):
            return _error_response("Each career must be a non-empty string.")

        normalized_careers: List[str] = []
        for career in careers:
            career_family = resolve_career_family(career)
            if not career_family:
                return _unsupported_role_error()
            normalized_careers.append(career_family)

        result = compare_careers(user_profile=user_profile, career_list=normalized_careers)
        result["disclaimer"] = STANDARD_DISCLAIMER
        result["confidence_level"] = _aggregate_confidence(
            [confidence_level_for(career) for career in normalized_careers]
        )
        return _to_json_safe(result)

    except FileNotFoundError:
        return _error_response(
            "Required model artifacts are missing. Please run the existing training pipeline first."
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except Exception:
        return _error_response(
            "Career View could not process this request right now. Please try again."
        )


if __name__ == "__main__":
    single_demo = run_career_view(
        user_profile={
            "career": "Data Analyst",
            "skills": ["sql", "python", "excel"],
            "location": "Bengaluru",
        }
    )
    print(single_demo)

    comparison_demo = run_career_view(
        user_profile={
            "skills": ["sql", "python", "excel"],
            "location": "Bengaluru",
        },
        careers=["Data Analyst", "Product Manager"],
    )
    print(comparison_demo)
