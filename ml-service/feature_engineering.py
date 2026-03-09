"""
Feature engineering for role-level master table.

Outputs:
- career_master table required by product spec.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from data_preprocessing import run_preprocessing


USD_TO_INR = 83.0  # Stable conversion for MVP benchmarking.
OUTPUT_PATH = Path("E:/Carrer View/ml-service/data/career_master.csv")


def _top_skills_for_role(skills_df: pd.DataFrame, role: str, top_n: int = 12) -> List[str]:
    rows = skills_df[skills_df["career_name"] == role]
    token_counter = Counter()
    for tokens in rows["skills_list"].tolist():
        token_counter.update(tokens)
    return [token for token, _ in token_counter.most_common(top_n)]


def _postings_count_for_role(job_desc_df: pd.DataFrame, skills_df: pd.DataFrame, role: str) -> int:
    count_1 = int((job_desc_df["career_name"] == role).sum())
    count_2 = int((skills_df["career_name"] == role).sum())
    return count_1 + count_2


def _salary_distribution_inr(india_market: pd.DataFrame, ds_salary: pd.DataFrame, role: str) -> np.ndarray:
    salary_inr_india = india_market.loc[india_market["career_name"] == role, "salary_inr_annual"].values
    salary_inr_ds = ds_salary.loc[ds_salary["career_name"] == role, "salary_usd"].values * USD_TO_INR
    merged = np.concatenate([salary_inr_india, salary_inr_ds]) if len(salary_inr_ds) else salary_inr_india
    if len(merged) == 0:
        return np.array([])
    return merged[~np.isnan(merged)]


def build_career_master() -> pd.DataFrame:
    data = run_preprocessing()

    all_roles = sorted(
        set(data.job_descriptions["career_name"])
        | set(data.india_market["career_name"])
        | set(data.ds_salary["career_name"])
        | set(data.job_skills["career_name"])
    )

    records: List[Dict] = []
    postings_raw = []
    skills_raw = []

    # First pass to collect raw counts for min-max normalization.
    for role in all_roles:
        top_skills = _top_skills_for_role(data.job_skills, role)
        postings_count = _postings_count_for_role(data.job_descriptions, data.job_skills, role)
        postings_raw.append(postings_count)
        skills_raw.append(len(top_skills))

    max_postings = max(postings_raw) if postings_raw else 1
    max_skills = max(skills_raw) if skills_raw else 1

    for role in all_roles:
        top_skills = _top_skills_for_role(data.job_skills, role)
        salary_values = _salary_distribution_inr(data.india_market, data.ds_salary, role)
        postings_count = _postings_count_for_role(data.job_descriptions, data.job_skills, role)

        if len(salary_values) > 0:
            avg_salary = float(np.mean(salary_values))
            p25 = float(np.percentile(salary_values, 25))
            p75 = float(np.percentile(salary_values, 75))
        else:
            avg_salary = np.nan
            p25 = np.nan
            p75 = np.nan

        # Demand proxy combines posting frequency and skill richness.
        demand_score = (
            0.7 * (postings_count / max_postings if max_postings else 0.0)
            + 0.3 * (len(top_skills) / max_skills if max_skills else 0.0)
        )

        locations = sorted(
            set(data.india_market.loc[data.india_market["career_name"] == role, "location_clean"])
            | set(data.ds_salary.loc[data.ds_salary["career_name"] == role, "location_clean"])
        )

        records.append(
            {
                "career_name": role,
                "top_skills": ",".join(top_skills),
                "avg_salary": avg_salary,
                "salary_p25": p25,
                "salary_p75": p75,
                "salary_range": f"{int(p25) if not np.isnan(p25) else 0}-{int(p75) if not np.isnan(p75) else 0}",
                "demand_score": round(float(demand_score), 4),
                "locations": ",".join(locations),
                "postings_count": postings_count,
                "skills_count": len(top_skills),
            }
        )

    career_master = pd.DataFrame(records)
    # Fill missing salary stats with global median to keep model trainable.
    global_salary_median = float(career_master["avg_salary"].median(skipna=True))
    for col in ["avg_salary", "salary_p25", "salary_p75"]:
        career_master[col] = career_master[col].fillna(global_salary_median)

    career_master.to_csv(OUTPUT_PATH, index=False)
    return career_master


if __name__ == "__main__":
    df = build_career_master()
    print(f"career_master created: {OUTPUT_PATH}")
    print(df.head(10).to_string(index=False))
