"""
Data loading and cleaning for AI Career Simulator MVP.

WHY this file exists:
- We need one trusted place that reads only approved local datasets.
- We normalize noisy text fields early so downstream modeling stays stable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


BASE_DATA_DIR = Path("E:/Carrer View/ml-service/data")
JOB_DESC_PATH = BASE_DATA_DIR / "extracted_1/job_title_des.csv"
INDIA_MARKET_PATH = BASE_DATA_DIR / "extracted_2/job_market_india.csv"
DS_SALARY_PATH = BASE_DATA_DIR / "extracted_3/Data Science Jobs Salaries.csv"
JOB_SKILLS_PATH = BASE_DATA_DIR / "extracted_4/all_job_post.csv"
MERGED_OPTIONAL_PATH = BASE_DATA_DIR / "career_training_data.csv"


EXPECTED_SCHEMAS = {
    "job_descriptions": {"Job Title", "Job Description"},
    "india_market": {"Job Title", "Location", "Salary", "Monthly Salary", "Locality", "State"},
    "ds_salary": {
        "work_year",
        "experience_level",
        "employment_type",
        "job_title",
        "salary",
        "salary_currency",
        "salary_in_usd",
        "employee_residence",
        "remote_ratio",
        "company_location",
        "company_size",
    },
    "job_skills": {"job_id", "category", "job_title", "job_description", "job_skill_set"},
    "merged_optional": {
        "education_level",
        "degree_stream",
        "skills",
        "location",
        "interests",
        "risk_preference",
        "years_experience",
        "salary",
        "demand_label",
        "next_role_success",
        "burnout_label",
    },
}


TITLE_ALIAS_RULES = [
    (r"\bii+\b", ""),  # remove roman numeral suffixes like "ii", "iii"
    (r"\b(sr|senior)\b", "senior"),
    (r"\b(jr|junior)\b", "junior"),
    (r"\bml\b", "machine learning"),
    (r"\bai\b", "artificial intelligence"),
    (r"\bdevops engineer\b", "devops engineer"),
    (r"\bsoftware developer\b", "software engineer"),
    (r"\bdata scientist\b", "data scientist"),
    (r"\bdata analyst\b", "data analyst"),
]


@dataclass
class CleanedDataBundle:
    job_descriptions: pd.DataFrame
    india_market: pd.DataFrame
    ds_salary: pd.DataFrame
    job_skills: pd.DataFrame
    merged_optional: Optional[pd.DataFrame]


def normalize_text(value: object) -> str:
    text = str(value) if value is not None else ""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s/+\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_job_title(title: object) -> str:
    normalized = normalize_text(title)
    for pattern, replacement in TITLE_ALIAS_RULES:
        normalized = re.sub(pattern, replacement, normalized).strip()
        normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def parse_skill_tokens(skill_blob: object) -> List[str]:
    if pd.isna(skill_blob):
        return []
    raw = normalize_text(skill_blob).replace("/", ",")
    raw = raw.replace("|", ",").replace(";", ",")
    tokens = [
        t.strip()
        for t in raw.split(",")
        if t.strip() and t.strip() not in {"nan", "none", "null", "na"}
    ]
    deduped = sorted(set(tokens))
    return deduped


def parse_salary_to_inr(value: object) -> Optional[float]:
    """
    Convert noisy salary text to an approximate annual INR value.

    WHY approximate:
    - Source mixes monthly/annual and symbols.
    - For MVP we prioritize robust conversion over perfect precision.
    """
    if pd.isna(value):
        return None

    text = str(value).lower().strip()
    text = text.replace(",", "")
    nums = [float(x) for x in re.findall(r"\d+\.?\d*", text)]
    if not nums:
        return None

    base = sum(nums) / len(nums)
    if "k" in text:
        base *= 1_000
    if "lakh" in text or "lac" in text:
        base *= 100_000
    if "crore" in text:
        base *= 10_000_000

    # Assume monthly if explicit monthly clue appears.
    if "month" in text or "/mo" in text:
        base *= 12

    return float(base)


def _validate_columns(df: pd.DataFrame, required: Iterable[str], dataset_name: str) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"{dataset_name} missing columns: {missing}")


def validate_and_load_raw() -> Dict[str, pd.DataFrame]:
    job_desc = pd.read_csv(JOB_DESC_PATH)
    india_market = pd.read_csv(INDIA_MARKET_PATH)
    ds_salary = pd.read_csv(DS_SALARY_PATH)
    job_skills = pd.read_csv(JOB_SKILLS_PATH)

    _validate_columns(job_desc, EXPECTED_SCHEMAS["job_descriptions"], "job_descriptions")
    _validate_columns(india_market, EXPECTED_SCHEMAS["india_market"], "india_market")
    _validate_columns(ds_salary, EXPECTED_SCHEMAS["ds_salary"], "ds_salary")
    _validate_columns(job_skills, EXPECTED_SCHEMAS["job_skills"], "job_skills")

    merged_optional = None
    if MERGED_OPTIONAL_PATH.exists():
        merged_optional = pd.read_csv(MERGED_OPTIONAL_PATH)
        _validate_columns(merged_optional, EXPECTED_SCHEMAS["merged_optional"], "merged_optional")

    return {
        "job_descriptions": job_desc,
        "india_market": india_market,
        "ds_salary": ds_salary,
        "job_skills": job_skills,
        "merged_optional": merged_optional,
    }


def clean_dataframes(raw: Dict[str, pd.DataFrame]) -> CleanedDataBundle:
    job_desc = raw["job_descriptions"].copy()
    india_market = raw["india_market"].copy()
    ds_salary = raw["ds_salary"].copy()
    job_skills = raw["job_skills"].copy()
    merged_optional = raw.get("merged_optional")

    # Normalize titles across all role-bearing datasets.
    job_desc["career_name"] = job_desc["Job Title"].map(normalize_job_title)
    job_desc["job_description_clean"] = job_desc["Job Description"].map(normalize_text)
    job_desc = job_desc.drop_duplicates(subset=["career_name", "job_description_clean"])

    india_market["career_name"] = india_market["Job Title"].map(normalize_job_title)
    india_market["location_clean"] = india_market["Location"].map(normalize_text)
    india_market["salary_inr_annual"] = india_market["Salary"].map(parse_salary_to_inr)
    # Fill gaps with provided monthly salary converted to annual.
    india_market["salary_inr_annual"] = india_market["salary_inr_annual"].fillna(
        india_market["Monthly Salary"].fillna(0) * 12
    )
    india_market = india_market[india_market["salary_inr_annual"] > 0]

    ds_salary["career_name"] = ds_salary["job_title"].map(normalize_job_title)
    ds_salary["location_clean"] = ds_salary["company_location"].map(normalize_text)
    ds_salary["salary_usd"] = pd.to_numeric(ds_salary["salary_in_usd"], errors="coerce")
    ds_salary = ds_salary.dropna(subset=["salary_usd"])

    job_skills["career_name"] = job_skills["job_title"].map(normalize_job_title)
    job_skills["job_description_clean"] = job_skills["job_description"].map(normalize_text)
    job_skills["skills_list"] = job_skills["job_skill_set"].map(parse_skill_tokens)
    job_skills = job_skills[job_skills["career_name"] != ""]

    if merged_optional is not None:
        merged_optional = merged_optional.copy()
        merged_optional["skills"] = merged_optional["skills"].fillna("").map(parse_skill_tokens)
        merged_optional["location"] = merged_optional["location"].map(normalize_text)
        merged_optional["salary"] = pd.to_numeric(merged_optional["salary"], errors="coerce")
        merged_optional = merged_optional.dropna(subset=["salary"])

    return CleanedDataBundle(
        job_descriptions=job_desc,
        india_market=india_market,
        ds_salary=ds_salary,
        job_skills=job_skills,
        merged_optional=merged_optional,
    )


def validate_optional_merged_cleanliness(df: pd.DataFrame) -> Dict[str, float]:
    """
    Quick health checks for using merged file directly.
    """
    return {
        "rows": float(len(df)),
        "missing_salary_ratio": float(df["salary"].isna().mean()),
        "missing_skills_ratio": float((df["skills"].map(len) == 0).mean()),
        "unique_locations": float(df["location"].nunique()),
    }


def run_preprocessing() -> CleanedDataBundle:
    raw = validate_and_load_raw()
    return clean_dataframes(raw)


if __name__ == "__main__":
    data = run_preprocessing()
    print("Loaded and cleaned:")
    print(f"- job_descriptions: {data.job_descriptions.shape}")
    print(f"- india_market: {data.india_market.shape}")
    print(f"- ds_salary: {data.ds_salary.shape}")
    print(f"- job_skills: {data.job_skills.shape}")
    if data.merged_optional is not None:
        report = validate_optional_merged_cleanliness(data.merged_optional)
        print(f"- merged_optional: {data.merged_optional.shape}")
        print(f"- merged_health: {report}")
