"""
Career Action Plan Engine - step-by-step roadmap for a career path.

Generates school, college, early-career, and long-term steps
for a recommended combination of stream / degree / branch / career.
"""
from __future__ import annotations

from typing import Dict, Any, List


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "_")


SCHOOL_FOCUS = {
    "science": {
        "focus_subjects": ["math", "physics", "chemistry"],
        "skills_to_start": ["logical thinking", "basic programming", "problem solving"],
        "recommended_exams": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "COMEDK / state engineering exams"],
    },
    "commerce": {
        "focus_subjects": ["accountancy", "economics", "business studies", "math"],
        "skills_to_start": ["numerical reasoning", "communication", "basic spreadsheet skills"],
        "recommended_exams": ["CUET", "state commerce entrance exams"],
    },
    "arts": {
        "focus_subjects": ["english", "social sciences", "psychology / sociology"],
        "skills_to_start": ["writing", "critical thinking", "creative expression"],
        "recommended_exams": ["CUET", "design / media entrance exams"],
    },
    "vocational": {
        "focus_subjects": ["physics", "math", "vocational subjects"],
        "skills_to_start": ["hands-on skills", "tool usage", "safety awareness"],
        "recommended_exams": ["polytechnic / diploma entrance exams"],
    },
}


COLLEGE_ROADMAP_BY_BRANCH = {
    "computer_science": {
        "year_1": "Learn programming fundamentals (Python/Java), basic data structures and mathematics for CS.",
        "year_2": "Learn algorithms, databases, operating systems, and system design basics.",
        "year_3": "Build full-stack or backend projects, contribute to open source, and do internships.",
        "year_4": "Deepen expertise in a specialization (backend, full-stack, cloud, or ML) and prepare for interviews.",
    },
    "information_technology": {
        "year_1": "Learn networking basics, scripting, and SQL.",
        "year_2": "Learn databases, Linux, and cloud platform fundamentals.",
        "year_3": "Work on infrastructure / cloud projects and internships.",
        "year_4": "Specialize in DevOps, cloud, or SRE and prepare for interviews.",
    },
    "cyber_security": {
        "year_1": "Learn networking, operating systems, and basic scripting.",
        "year_2": "Learn security fundamentals, cryptography, and common vulnerabilities.",
        "year_3": "Practice in labs / CTFs, get internships in security teams.",
        "year_4": "Specialize in penetration testing or security engineering and earn certifications.",
    },
    "ai_ml": {
        "year_1": "Learn Python, linear algebra, statistics, and calculus.",
        "year_2": "Learn machine learning algorithms and data preprocessing.",
        "year_3": "Build ML projects and participate in Kaggle or similar competitions.",
        "year_4": "Specialize in NLP, computer vision, or ML systems and prepare for ML interviews.",
    },
    "data_science": {
        "year_1": "Learn Python, SQL, statistics, and data visualization.",
        "year_2": "Learn machine learning, analytics tools, and dashboards.",
        "year_3": "Build analytics projects for real datasets and internships.",
        "year_4": "Specialize in advanced analytics or ML and prepare for data roles.",
    },
}


COLLEGE_ROADMAP_GENERIC = {
    "year_1": "Build strong foundations in core subjects and basic programming / tools.",
    "year_2": "Learn advanced topics for your degree and start small projects.",
    "year_3": "Do internships, hackathons, and build real-world projects.",
    "year_4": "Specialize in a domain and prepare for placements or higher studies.",
}


EARLY_CAREER_BY_CAREER = {
    "software_engineer": [
        "Intern / Trainee Software Engineer",
        "Junior Software Engineer",
        "Backend or Full Stack Developer",
    ],
    "data_scientist": [
        "Data Science Intern",
        "Junior Data Scientist",
        "Machine Learning Engineer",
    ],
    "data_analyst": [
        "Data Analyst Intern",
        "Business / Data Analyst",
        "Reporting Analyst",
    ],
    "product_manager": [
        "Product Analyst",
        "Associate Product Manager",
        "Product Manager",
    ],
}


LONG_TERM_GROWTH_BY_CAREER = {
    "software_engineer": [
        "Senior Software Engineer",
        "Staff / Principal Engineer",
        "Engineering Manager or Architect",
    ],
    "data_scientist": [
        "Senior Data Scientist",
        "Lead Data Scientist / ML Architect",
        "Head of Data / Director of Data Science",
    ],
    "data_analyst": [
        "Senior Data Analyst",
        "Analytics Manager",
        "Director of Analytics / BI",
    ],
    "product_manager": [
        "Senior Product Manager",
        "Group Product Manager",
        "Director / VP of Product",
    ],
}


def generate_action_plan(recommended_path: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a structured action plan for a recommended path.

    Input shape:
        {
            "stream": "science",
            "degree": "engineering",
            "branch": "computer_science",
            "career": "software_engineer"
        }
    """
    stream = _norm(recommended_path.get("stream"))
    degree = _norm(recommended_path.get("degree"))
    branch = _norm(recommended_path.get("branch"))
    career = _norm(recommended_path.get("career"))

    # 1) School preparation
    school_prep = SCHOOL_FOCUS.get(
        stream or "science",
        {
            "focus_subjects": ["math", "english"],
            "skills_to_start": ["logical thinking", "communication"],
            "recommended_exams": [],
        },
    )

    # 2) College preparation
    if branch in COLLEGE_ROADMAP_BY_BRANCH:
        college_prep = COLLEGE_ROADMAP_BY_BRANCH[branch]
    else:
        college_prep = COLLEGE_ROADMAP_GENERIC

    # 3) Early career steps
    if career in EARLY_CAREER_BY_CAREER:
        early_career_steps: List[str] = EARLY_CAREER_BY_CAREER[career]
    else:
        # Fallback based on branch/degree
        if branch in {"computer_science", "information_technology", "cyber_security", "electronics", "mechanical"}:
            early_career_steps = [
                "Intern / Trainee Engineer",
                "Junior Engineer / Developer",
                "Engineer / Developer",
            ]
        elif branch in {"ai_ml", "data_science"} or degree in {"data_science", "statistics"}:
            early_career_steps = [
                "Data / ML Intern",
                "Junior Data Scientist / Analyst",
                "Data Scientist / Analyst",
            ]
        else:
            early_career_steps = [
                "Intern / Trainee",
                "Junior Associate",
                "Associate / Engineer",
            ]

    # 4) Long-term growth
    if career in LONG_TERM_GROWTH_BY_CAREER:
        long_term_growth: List[str] = LONG_TERM_GROWTH_BY_CAREER[career]
    else:
        if branch in {"computer_science", "information_technology", "cyber_security", "electronics", "mechanical"}:
            long_term_growth = [
                "Senior Engineer",
                "Lead / Principal Engineer",
                "Engineering Manager or Architect",
            ]
        elif branch in {"ai_ml", "data_science"} or degree in {"data_science", "statistics"}:
            long_term_growth = [
                "Senior Data Scientist / Analyst",
                "Lead Data / ML Engineer",
                "Head of Data / Analytics",
            ]
        else:
            long_term_growth = [
                "Senior Professional",
                "Team Lead / Manager",
                "Director / Head of Function",
            ]

    return {
        "school_preparation": school_prep,
        "college_preparation": college_prep,
        "early_career_steps": early_career_steps,
        "long_term_growth": long_term_growth,
    }

