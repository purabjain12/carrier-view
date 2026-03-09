"""
Explanation layer powered by local Hugging Face cached Q&A dataset.

IMPORTANT:
- This module is for explanation only (not prediction/training).
"""

from __future__ import annotations

import os
from difflib import get_close_matches
from typing import Dict, List

import pandas as pd
from datasets import load_dataset

from data_preprocessing import normalize_job_title


HF_DATASET_NAME = "Pradeep016/career-guidance-qa-dataset"


def load_guidance_dataset() -> pd.DataFrame:
    # Force offline behavior; dataset is already cached locally.
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    ds = load_dataset(HF_DATASET_NAME)
    df = ds["train"].to_pandas()
    df["role_norm"] = df["role"].map(normalize_job_title)
    return df


def _find_best_role_match(role_norm: str, role_pool: List[str]) -> str:
    if role_norm in role_pool:
        return role_norm
    close = get_close_matches(role_norm, role_pool, n=1, cutoff=0.6)
    return close[0] if close else ""


def build_explanation(career_name: str, top_skills: List[str]) -> Dict[str, object]:
    role_norm = normalize_job_title(career_name)
    qa_df = load_guidance_dataset()
    role_pool = sorted(qa_df["role_norm"].dropna().unique().tolist())
    matched_role = _find_best_role_match(role_norm, role_pool)

    if not matched_role:
        return {
            "why_this_career": (
                f"{career_name.title()} matches your skill profile and market demand. "
                "A more specific Q&A match was not found in the guidance dataset."
            ),
            "summary": (
                f"{career_name.title()} is projected as a viable path. "
                "Focus on core skills and market-relevant projects."
            ),
            "common_qa": [],
        }

    role_rows = qa_df[qa_df["role_norm"] == matched_role].head(4)
    common_qa = [
        {"question": row["question"], "answer": row["answer"]}
        for _, row in role_rows.iterrows()
    ]

    skills_preview = ", ".join(top_skills[:4]) if top_skills else "foundational skills"
    return {
        "why_this_career": (
            f"{career_name.title()} aligns with your current profile and demand signals. "
            f"Your strongest leverage comes from {skills_preview}."
        ),
        "summary": (
            f"{career_name.title()} has practical growth potential when paired with continuous "
            "skill upgrades and location-aware opportunities."
        ),
        "common_qa": common_qa,
    }


if __name__ == "__main__":
    response = build_explanation("Data Analyst", ["sql", "python", "excel", "statistics"])
    print(response)
