"""
Career Navigation Engine - routes by career stage.

Stages:
- after_10th: stream recommendation
- after_12th: degree recommendation
- college_student: branch recommendation
- working_professional: delegate to existing simulation (handled in career_view_service)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .branch_recommender import load_branch_career_dataset, recommend_branch
from .career_action_plan_engine import generate_action_plan
from .career_coach_engine import generate_career_guidance
from .degree_recommender import recommend_degree
from .stream_recommender import recommend_stream


VALID_STAGES = frozenset({"after_10th", "after_12th", "college_student", "working_professional"})


def _safe_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if x is not None and str(x).strip()]
    return []


def _branch_to_career(branch: str) -> Optional[str]:
    """Map engineering branch to career_family for guidance."""
    try:
        df = load_branch_career_dataset()
        branch_norm = str(branch or "").strip().lower().replace(" ", "_")
        row = df[df["branch"].fillna("").str.strip().str.lower() == branch_norm]
        if row.empty:
            return None
        cf = str(row.iloc[0].get("career_family", "")).strip().lower()
        return cf if cf else None
    except Exception:
        return None


def _safe_str(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return s.lower().replace(" ", "_") if s else ""


def navigate_career(stage: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route navigation by career stage.
    working_professional returns empty navigation (simulation handled upstream).
    """
    stage = _safe_str(stage) or "working_professional"
    if stage not in VALID_STAGES:
        stage = "working_professional"

    interests = _safe_list(user_profile.get("interests"))
    skills = _safe_list(user_profile.get("skills"))
    stream = _safe_str(user_profile.get("stream"))

    if stage == "after_10th":
        out = recommend_stream(interests=interests, skills=skills)
        out["stage"] = "after_10th"
        recommended_path = {
            "stream": out.get("recommended_streams", [None])[0] if out.get("recommended_streams") else None,
            "degree": out.get("future_paths", [None])[0] if out.get("future_paths") else None,
            "branch": None,
            "career": None,
        }
        guidance = generate_career_guidance(user_profile=user_profile, recommended_path=recommended_path)
        out["reasoning"] = guidance.get("reasoning", out.get("reason", ""))
        out["skills_to_develop"] = guidance.get("skills_to_develop", [])
        out["learning_roadmap"] = guidance.get("learning_roadmap", {})
        out["future_roles"] = guidance.get("future_roles", out.get("future_paths", []))
        out["action_plan"] = generate_action_plan(recommended_path)
        return _sanitize_navigation_output(out)

    if stage == "after_12th":
        stream = stream or (interests[0] if interests else "science")
        out = recommend_degree(stream=stream, interests=interests)
        out["stage"] = "after_12th"
        recommended_path = {
            "stream": stream,
            "degree": out.get("recommended_degrees", [None])[0] if out.get("recommended_degrees") else None,
            "branch": None,
            "career": None,
        }
        guidance = generate_career_guidance(user_profile=user_profile, recommended_path=recommended_path)
        out["reasoning"] = guidance.get("reasoning", "")
        out["skills_to_develop"] = guidance.get("skills_to_develop", [])
        out["learning_roadmap"] = guidance.get("learning_roadmap", {})
        out["future_roles"] = guidance.get("future_roles", [])
        out["action_plan"] = generate_action_plan(recommended_path)
        return _sanitize_navigation_output(out)

    if stage == "college_student":
        out = recommend_branch(skills=skills, interests=interests)
        out["stage"] = "college_student"
        top_branch = out.get("recommended_branches", [None])[0] if out.get("recommended_branches") else None
        career_from_branch = _branch_to_career(top_branch) if top_branch else None
        recommended_path = {
            "stream": stream or None,
            "degree": None,
            "branch": top_branch,
            "career": career_from_branch,
        }
        guidance = generate_career_guidance(user_profile=user_profile, recommended_path=recommended_path)
        out["reasoning"] = guidance.get("reasoning", "")
        out["skills_to_develop"] = guidance.get("skills_to_develop", out.get("required_skills", []))
        out["learning_roadmap"] = guidance.get("learning_roadmap", {})
        out["future_roles"] = guidance.get("future_roles", [])
        out["action_plan"] = generate_action_plan(recommended_path)
        return _sanitize_navigation_output(out)

    return {"stage": "working_professional", "use_simulation": True}


def _sanitize_navigation_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure no NaN, None, or invalid values in output."""
    import math
    result: Dict[str, Any] = {}
    for k, v in data.items():
        if v is None:
            if k in ("stage", "stream", "reason"):
                result[k] = ""
            elif k in ("recommended_streams", "recommended_degrees", "recommended_branches", "future_paths", "required_skills", "skills_to_develop", "future_roles"):
                result[k] = []
            else:
                result[k] = v
        elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            result[k] = 0.0
        elif isinstance(v, list):
            cleaned = []
            for x in v:
                if x is None:
                    continue
                if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
                    continue
                s = str(x).strip()
                if s:
                    cleaned.append(s)
            result[k] = cleaned
        else:
            result[k] = v
    return result
