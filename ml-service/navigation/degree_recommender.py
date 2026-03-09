"""
Degree recommender for after-12th students.
Maps stream to available degree paths.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


NAV_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "navigation"
STREAM_DEGREE_PATH = NAV_DATA_DIR / "stream_degree_paths.csv"

_degree_df: pd.DataFrame | None = None


def _normalize(x: str) -> str:
    return str(x or "").strip().lower().replace(" ", "_")


def load_degree_dataset() -> pd.DataFrame:
    global _degree_df
    if _degree_df is not None:
        return _degree_df
    if not STREAM_DEGREE_PATH.exists():
        raise FileNotFoundError(f"Missing {STREAM_DEGREE_PATH}")
    df = pd.read_csv(STREAM_DEGREE_PATH)
    _degree_df = df
    return df


def recommend_degree(stream: str, interests: List[str]) -> Dict:
    """
    Return available degrees for the given stream.
    Interests used for optional ranking; all degrees for stream returned.
    """
    stream = _normalize(stream)
    interests = [i for i in (interests or []) if i and str(i).strip()]
    interest_set = set(_normalize(i) for i in interests)

    df = load_degree_dataset()
    df = df[df["stream"].fillna("").str.strip().str.lower() == stream]
    degrees = df["degree"].dropna().unique().tolist()
    degrees = [str(d).strip().lower() for d in degrees if d]

    if not degrees:
        degrees = ["engineering", "business", "science"]

    return {
        "stream": stream,
        "recommended_degrees": degrees,
    }
