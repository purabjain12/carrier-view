"""
Authoritative supported career scope for Career View v1.

WHY this exists:
- Product trust depends on clear boundaries and explicit support.
- This file is the single source of truth for what users can request.
"""

from __future__ import annotations

import re
from typing import Optional


STANDARD_DISCLAIMER = (
    "Career View simulates realistic outcomes based on current market data. "
    "Results are guidance, not guarantees."
)


SUPPORTED_CAREER_FAMILIES = {
    "software_engineer": "Software Engineer",
    "data_analyst": "Data Analyst",
    "data_scientist": "Data Scientist",
    "product_manager": "Product Manager (Tech)",
}


# Product scope for v1 specialization depth.
SOFTWARE_ENGINEER_SPECIALIZATIONS = {
    "web_development": "Web Development",
    "backend": "Backend",
    "full_stack": "Full Stack",
    "devops": "DevOps",
    "cloud": "Cloud",
    "cyber_security": "Cyber Security",
    "qa_testing": "QA / Testing",
}


CAREER_ALIASES = {
    "software engineer": "software_engineer",
    "software_engineer": "software_engineer",
    "data analyst": "data_analyst",
    "data_analyst": "data_analyst",
    "data scientist": "data_scientist",
    "data_scientist": "data_scientist",
    "product manager": "product_manager",
    "product_manager": "product_manager",
    "product manager tech": "product_manager",
    "product_manager_tech": "product_manager",
}


SPECIALIZATION_ALIASES = {
    "web development": "web_development",
    "web_development": "web_development",
    "web developer": "web_development",
    "backend": "backend",
    "backend developer": "backend",
    "backend_developer": "backend",
    "full stack": "full_stack",
    "fullstack": "full_stack",
    "fullstack developer": "full_stack",
    "fullstack_developer": "full_stack",
    "devops": "devops",
    "devops engineer": "devops",
    "devops_engineer": "devops",
    "cloud": "cloud",
    "cloud engineer": "cloud",
    "cloud_engineer": "cloud",
    "cyber security": "cyber_security",
    "cyber_security": "cyber_security",
    "cyber security engineer": "cyber_security",
    "cyber_security_engineer": "cyber_security",
    "qa testing": "qa_testing",
    "qa / testing": "qa_testing",
    "qa_engineer": "qa_testing",
    "testing": "qa_testing",
}


def normalize_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def resolve_career_family(value: str) -> Optional[str]:
    normalized = normalize_key(value)
    if normalized in SUPPORTED_CAREER_FAMILIES:
        return normalized
    return CAREER_ALIASES.get(value.strip().lower()) or CAREER_ALIASES.get(
        normalized.replace("_", " ")
    )


def resolve_specialization(value: str) -> Optional[str]:
    normalized = normalize_key(value)
    if normalized in SOFTWARE_ENGINEER_SPECIALIZATIONS:
        return normalized
    return SPECIALIZATION_ALIASES.get(value.strip().lower()) or SPECIALIZATION_ALIASES.get(
        normalized.replace("_", " ")
    )


def is_specialization_supported_for_family(specialization: str, career_family: str) -> bool:
    return (
        normalize_key(career_family) == "software_engineer"
        and normalize_key(specialization) in SOFTWARE_ENGINEER_SPECIALIZATIONS
    )


def confidence_level_for(career_family: str, specialization: Optional[str] = None) -> str:
    family = normalize_key(career_family)
    spec = normalize_key(specialization or "")
    if family in SUPPORTED_CAREER_FAMILIES and spec:
        return "Medium"
    if family in SUPPORTED_CAREER_FAMILIES:
        return "High"
    return "Low"
