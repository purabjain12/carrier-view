"""
Career specialization configuration for CS depth expansion.

WHY this file exists:
- Product expands within existing career families without retraining models.
- Keeps specialization behavior transparent, tunable, and deterministic.
"""

from __future__ import annotations

from typing import Dict, Optional


def normalize_key(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


CS_SPECIALIZATIONS: Dict[str, Dict] = {
    # Software Engineer family
    "web_development": {
        "parent_family": "software_engineer",
        "primary_skill_emphasis": ["javascript", "react", "html", "css"],
        "stability_modifier": -0.01,
        "growth_modifier": 1.04,
        "risk_modifier": 1.08,
    },
    "backend": {
        "parent_family": "software_engineer",
        "primary_skill_emphasis": ["api", "databases", "python", "java"],
        "stability_modifier": 0.02,
        "growth_modifier": 1.02,
        "risk_modifier": 0.98,
    },
    "full_stack": {
        "parent_family": "software_engineer",
        "primary_skill_emphasis": ["frontend", "backend", "system_design"],
        "stability_modifier": 0.01,
        "growth_modifier": 1.03,
        "risk_modifier": 1.03,
    },
    "devops": {
        "parent_family": "software_engineer",
        "primary_skill_emphasis": ["devops", "cloud", "automation", "kubernetes"],
        "stability_modifier": 0.04,
        "growth_modifier": 0.99,
        "risk_modifier": 0.92,
    },
    "cloud": {
        "parent_family": "software_engineer",
        "primary_skill_emphasis": ["cloud", "aws", "gcp", "architecture"],
        "stability_modifier": 0.03,
        "growth_modifier": 1.01,
        "risk_modifier": 0.95,
    },
    "cyber_security": {
        "parent_family": "software_engineer",
        "primary_skill_emphasis": ["security", "networking", "incident_response"],
        "stability_modifier": 0.05,
        "growth_modifier": 0.97,
        "risk_modifier": 0.90,
    },
    "qa_testing": {
        "parent_family": "software_engineer",
        "primary_skill_emphasis": ["testing", "automation", "quality"],
        "stability_modifier": 0.03,
        "growth_modifier": 0.98,
        "risk_modifier": 0.94,
    },
    # Data Scientist family
    "ml_engineer": {
        "parent_family": "data_scientist",
        "primary_skill_emphasis": ["machine_learning", "mlops", "python"],
        "stability_modifier": -0.01,
        "growth_modifier": 1.07,
        "risk_modifier": 1.12,
    },
    "data_engineer": {
        "parent_family": "data_scientist",
        "primary_skill_emphasis": ["pipelines", "spark", "sql", "warehousing"],
        "stability_modifier": 0.03,
        "growth_modifier": 1.03,
        "risk_modifier": 0.96,
    },
    "research_scientist": {
        "parent_family": "data_scientist",
        "primary_skill_emphasis": ["research", "statistics", "experimentation"],
        "stability_modifier": -0.02,
        "growth_modifier": 1.06,
        "risk_modifier": 1.15,
    },
}


def get_specialization_config(
    specialization: str, career_family: str
) -> Optional[Dict]:
    """
    Return specialization config only when it belongs to the selected career family.
    """
    spec_key = normalize_key(specialization)
    family_key = normalize_key(career_family)
    cfg = CS_SPECIALIZATIONS.get(spec_key)
    if not cfg:
        return None
    if normalize_key(cfg.get("parent_family", "")) != family_key:
        return None
    return cfg
