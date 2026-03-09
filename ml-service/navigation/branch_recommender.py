"""
Engineering branch recommender for college students.
Matches skills and interests to branch options.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


NAV_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "navigation"
BRANCHES_PATH = NAV_DATA_DIR / "engineering_branches.csv"
BRANCH_CAREER_PATH = NAV_DATA_DIR / "branch_career_paths.csv"

_branch_df: pd.DataFrame | None = None
_career_df: pd.DataFrame | None = None


def _normalize(x: str) -> str:
    return str(x or "").strip().lower().replace(" ", "_")


def _split_pipe(val: object) -> List[str]:
    if pd.isna(val):
        return []
    return [t.strip().lower() for t in str(val).split("|") if t.strip()]


def load_branch_dataset() -> pd.DataFrame:
    global _branch_df
    if _branch_df is not None:
        return _branch_df
    if not BRANCHES_PATH.exists():
        raise FileNotFoundError(f"Missing {BRANCHES_PATH}")
    df = pd.read_csv(BRANCHES_PATH)
    _branch_df = df
    return df


def load_branch_career_dataset() -> pd.DataFrame:
    global _career_df
    if _career_df is not None:
        return _career_df
    if not BRANCH_CAREER_PATH.exists():
        raise FileNotFoundError(f"Missing {BRANCH_CAREER_PATH}")
    df = pd.read_csv(BRANCH_CAREER_PATH)
    _career_df = df
    return df


def recommend_branch(skills: List[str], interests: List[str]) -> Dict:
    """
    Recommend top engineering branches based on skill and interest overlap.
    Maps branches to career_family for downstream simulation.
    """
    skills = [s for s in (skills or []) if s and str(s).strip()]
    interests = [i for i in (interests or []) if i and str(i).strip()]
    skill_tokens = set(_normalize(s) for s in skills)
    interest_tokens = set(_normalize(i) for i in interests)

    df = load_branch_dataset()
    career_df = load_branch_career_dataset()
    branch_to_career = dict(
        zip(
            career_df["branch"].fillna("").str.strip().str.lower(),
            career_df["career_family"].fillna("").str.strip().str.lower(),
        )
    )

    scores: List[tuple] = []
    for _, row in df.iterrows():
        branch = str(row.get("branch", "")).strip().lower()
        if not branch:
            continue
        skill_col = _split_pipe(row.get("skill_keywords", ""))
        interest_col = _split_pipe(row.get("interest_keywords", ""))

        s_overlap = len(skill_tokens.intersection(set(skill_col))) if skill_tokens else 0
        i_overlap = len(interest_tokens.intersection(set(interest_col))) if interest_tokens else 0
        score = s_overlap * 1.2 + i_overlap
        if not skill_tokens and not interest_tokens:
            score = 1.0
        scores.append((branch, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_branches = [t[0] for t in scores[:5]]
    required_skills = []
    for b in top_branches[:2]:
        row = df[df["branch"].fillna("").str.strip().str.lower() == b]
        if not row.empty:
            required_skills.extend(_split_pipe(row.iloc[0].get("skill_keywords", "")))

    return {
        "recommended_branches": top_branches,
        "required_skills": list(dict.fromkeys(required_skills))[:8],
    }
