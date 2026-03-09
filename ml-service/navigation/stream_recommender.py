"""
Stream recommender for after-10th students.
Matches interests and skills to 10+2 stream options.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


NAV_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "navigation"
STREAM_GUIDANCE_PATH = NAV_DATA_DIR / "stream_guidance.csv"

_stream_df: pd.DataFrame | None = None


def _normalize(x: str) -> str:
    return str(x or "").strip().lower().replace(" ", "_")


def _split_pipe(val: object) -> List[str]:
    if pd.isna(val):
        return []
    return [t.strip().lower() for t in str(val).split("|") if t.strip()]


def load_stream_dataset() -> pd.DataFrame:
    global _stream_df
    if _stream_df is not None:
        return _stream_df
    if not STREAM_GUIDANCE_PATH.exists():
        raise FileNotFoundError(f"Missing {STREAM_GUIDANCE_PATH}")
    df = pd.read_csv(STREAM_GUIDANCE_PATH)
    _stream_df = df
    return df


def recommend_stream(interests: List[str], skills: List[str]) -> Dict:
    """
    Recommend top 2 streams based on interest and skill overlap.
    """
    interests = [i for i in (interests or []) if i and str(i).strip()]
    skills = [s for s in (skills or []) if s and str(s).strip()]

    df = load_stream_dataset()
    interest_tokens = set(_normalize(i) for i in interests)
    skill_tokens = set(_normalize(s) for s in skills)

    scores: List[tuple] = []
    for _, row in df.iterrows():
        stream = str(row.get("stream", "")).strip().lower()
        if not stream:
            continue
        interest_col = _split_pipe(row.get("interest_keywords", ""))
        skill_col = _split_pipe(row.get("skill_keywords", ""))
        future_col = _split_pipe(row.get("future_paths", ""))

        i_overlap = len(interest_tokens.intersection(set(interest_col))) if interest_tokens else 0
        s_overlap = len(skill_tokens.intersection(set(skill_col))) if skill_tokens else 0
        score = i_overlap * 1.5 + s_overlap
        if not interest_tokens and not skill_tokens:
            score = 1.0
        scores.append((stream, score, future_col))

    scores.sort(key=lambda x: x[1], reverse=True)
    top2 = [t[0] for t in scores[:2]]
    future_paths = list(scores[0][2]) if scores else []

    reason = (
        f"Based on your interests ({', '.join(interests[:3]) or 'general'}) "
        f"and skills ({', '.join(skills[:3]) or 'emerging'}), these streams fit best."
    )
    if not interests and not skills:
        reason = "We recommend science or commerce as broad options. Add interests and skills for better guidance."

    return {
        "recommended_streams": top2,
        "reason": reason,
        "future_paths": future_paths,
    }
