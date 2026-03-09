"""
Career Coach Engine - human-readable guidance for recommended paths.

Provides explanations and actionable guidance for users at each career stage.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _safe_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if x is not None and str(x).strip()]
    return []


def _safe_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip().replace("_", " ").lower() if str(val).strip() else ""


# Template-based guidance mappings for streams, degrees, branches, and careers
STREAM_SKILLS = {
    "science": ["math", "physics", "problem solving", "analytics", "research"],
    "commerce": ["accounting", "economics", "analytics", "communication", "management"],
    "arts": ["communication", "creative thinking", "writing", "research", "design"],
    "vocational": ["technical skills", "hands-on work", "problem solving", "tools", "certifications"],
}

STREAM_ROADMAP = {
    "science": {
        "year_1": "Build strong foundations in math, physics, chemistry",
        "year_2": "Deepen subject knowledge and analytical skills",
        "year_3": "Explore electives and career paths (engineering, medicine, research)",
        "year_4": "Choose degree stream and prepare for higher studies",
    },
    "commerce": {
        "year_1": "Build foundations in accounts, economics, business studies",
        "year_2": "Develop analytical and quantitative skills",
        "year_3": "Explore finance, management, and analytics paths",
        "year_4": "Choose degree stream (B.Com, BBA, CA, etc.)",
    },
    "arts": {
        "year_1": "Build foundations in chosen subjects",
        "year_2": "Develop communication and critical thinking",
        "year_3": "Explore design, media, psychology, or humanities paths",
        "year_4": "Choose degree stream and career direction",
    },
    "vocational": {
        "year_1": "Build technical foundations",
        "year_2": "Develop hands-on skills and certifications",
        "year_3": "Gain practical experience",
        "year_4": "Specialize and enter workforce",
    },
}

STREAM_REASONING = {
    "science": "Your interests align well with Science. This stream opens paths to engineering, medicine, research, and data-driven fields.",
    "commerce": "Your interests align well with Commerce. This stream opens paths to business, management, finance, and analytics roles.",
    "arts": "Your interests align well with Arts. This stream opens paths to design, media, psychology, and creative professions.",
    "vocational": "Your hands-on interests align well with Vocational studies. This stream opens paths to technical diplomas and skilled trades.",
}

DEGREE_REASONING = {
    "engineering": "Engineering builds strong problem-solving and technical foundations.",
    "medicine": "Medicine combines science with patient care and research.",
    "data_science": "Data Science bridges statistics, programming, and business analytics.",
    "pure_science": "Pure Science deepens research and analytical capabilities.",
    "research": "Research prepares you for academia and industry R&D.",
    "business": "Business develops management and analytical skills.",
    "mba": "MBA accelerates leadership and strategic thinking.",
    "accounting": "Accounting builds expertise in finance and compliance.",
    "economics": "Economics develops analytical and policy-oriented skills.",
    "design": "Design combines creativity with user-centered thinking.",
    "humanities": "Humanities strengthens communication and critical thinking.",
    "media": "Media connects content, technology, and audience.",
    "psychology": "Psychology develops understanding of human behaviour.",
    "diploma": "Diploma provides focused technical skills for immediate employability.",
    "certification": "Certification validates specialized skills.",
}

BRANCH_SKILLS = {
    "computer_science": ["programming", "data structures", "algorithms", "system design", "databases"],
    "information_technology": ["networking", "databases", "sql", "cloud", "devops"],
    "cyber_security": ["networking", "security fundamentals", "cryptography", "ethical hacking", "risk assessment"],
    "ai_ml": ["python", "machine learning", "statistics", "deep learning", "data pipelines"],
    "data_science": ["python", "sql", "statistics", "data visualization", "machine learning"],
    "electronics": ["circuits", "embedded systems", "signal processing", "hardware design"],
    "mechanical": ["cad", "design", "thermodynamics", "manufacturing", "analytics"],
}

BRANCH_ROADMAP = {
    "computer_science": {
        "year_1": "Learn programming fundamentals (Python/Java) and basic data structures",
        "year_2": "Learn algorithms, databases, and system design basics",
        "year_3": "Build projects, contribute to open source, and seek internships",
        "year_4": "Specialize in a domain (web, mobile, cloud, or AI)",
    },
    "information_technology": {
        "year_1": "Learn networking fundamentals, SQL, and scripting",
        "year_2": "Learn cloud platforms (AWS/Azure) and databases",
        "year_3": "Build infrastructure projects and internships",
        "year_4": "Specialize in cloud, DevOps, or security",
    },
    "cyber_security": {
        "year_1": "Learn networking, operating systems, and basic programming",
        "year_2": "Learn security fundamentals, cryptography, and ethical hacking",
        "year_3": "Practice in CTFs and security labs, internships",
        "year_4": "Specialize in penetration testing or security engineering",
    },
    "ai_ml": {
        "year_1": "Learn Python, linear algebra, statistics, and calculus",
        "year_2": "Learn machine learning, data preprocessing, and basic deep learning",
        "year_3": "Build ML projects and Kaggle competitions",
        "year_4": "Specialize in NLP, computer vision, or ML systems",
    },
    "data_science": {
        "year_1": "Learn Python, SQL, statistics, and data visualization",
        "year_2": "Learn machine learning and analytics tools",
        "year_3": "Build analytics projects and internships",
        "year_4": "Specialize in analytics, ML, or data engineering",
    },
    "electronics": {
        "year_1": "Learn circuits, embedded C, and basic electronics",
        "year_2": "Learn signal processing, microcontrollers, and PCB design",
        "year_3": "Build hardware projects and internships",
        "year_4": "Specialize in IoT, embedded systems, or VLSI",
    },
    "mechanical": {
        "year_1": "Learn CAD, thermodynamics, and mechanics",
        "year_2": "Learn manufacturing, design, and simulation",
        "year_3": "Build design projects and internships",
        "year_4": "Specialize in design, automation, or R&D",
    },
}

BRANCH_FUTURE_ROLES = {
    "computer_science": ["software engineer", "full stack developer", "backend engineer", "ml engineer"],
    "information_technology": ["software engineer", "cloud engineer", "devops engineer", "database administrator"],
    "cyber_security": ["security engineer", "penetration tester", "security analyst", "cyber security consultant"],
    "ai_ml": ["ml engineer", "data scientist", "ai researcher", "nlp engineer"],
    "data_science": ["data scientist", "data analyst", "ml engineer", "data engineer"],
    "electronics": ["embedded engineer", "hardware engineer", "systems engineer", "iot engineer"],
    "mechanical": ["design engineer", "manufacturing engineer", "mechanical engineer", "r&d engineer"],
}

CAREER_DISPLAY = {
    "software_engineer": "software engineer",
    "data_analyst": "data analyst",
    "data_scientist": "data scientist",
    "product_manager": "product manager",
}


def generate_career_guidance(
    user_profile: Dict[str, Any],
    recommended_path: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate human-readable guidance based on user profile and recommended path.

    Returns: reasoning, skills_to_develop, learning_roadmap, future_roles
    """
    interests = _safe_list(user_profile.get("interests"))
    skills = _safe_list(user_profile.get("skills"))
    education_level = _safe_str(user_profile.get("education_level"))
    degree_stream = _safe_str(user_profile.get("degree_stream"))

    stream = _safe_str(recommended_path.get("stream"))
    degree = _safe_str(recommended_path.get("degree"))
    branch = _safe_str(recommended_path.get("branch"))
    career = _safe_str(recommended_path.get("career"))

    # Build reasoning
    reasoning_parts: List[str] = []
    interest_text = ", ".join(interests[:3]) if interests else "your profile"
    skill_text = ", ".join(skills[:3]) if skills else "emerging skills"

    if stream:
        key = stream.replace(" ", "_")
        msg = STREAM_REASONING.get(key, f"Your interests in {interest_text} align well with {stream.replace('_', ' ').title()}.")
        reasoning_parts.append(msg)

    if degree and not branch:
        key = degree.replace(" ", "_")
        msg = DEGREE_REASONING.get(key, f"{degree.replace('_', ' ').title()} will build on your interests and skills.")
        reasoning_parts.append(msg)

    if branch:
        branch_norm = branch.replace(" ", "_")
        skills_list = BRANCH_SKILLS.get(branch_norm, ["programming", "analytics", "problem solving"])
        reasoning_parts.append(
            f"Your skills in {skill_text} align well with {branch.replace('_', ' ').title()}. "
            f"Focus on building expertise in {', '.join(skills_list[:3])}."
        )

    if career:
        career_display = CAREER_DISPLAY.get(career.replace(" ", "_"), career.replace("_", " "))
        reasoning_parts.append(f"This path leads toward roles like {career_display}.")

    reasoning = " ".join(reasoning_parts) if reasoning_parts else (
        f"Based on your interests ({interest_text}) and skills ({skill_text}), this path is a strong fit for you."
    )

    # Build skills_to_develop
    if branch:
        branch_norm = branch.replace(" ", "_")
        skills_to_develop = BRANCH_SKILLS.get(branch_norm, ["programming", "data structures", "analytics"])
    elif stream:
        stream_norm = stream.replace(" ", "_")
        skills_to_develop = STREAM_SKILLS.get(stream_norm, ["analytics", "problem solving", "communication"])
    else:
        skills_to_develop = ["programming", "data structures", "algorithms", "analytics"]

    # Build learning_roadmap
    if branch:
        branch_norm = branch.replace(" ", "_")
        learning_roadmap = BRANCH_ROADMAP.get(
            branch_norm,
            {
                "year_1": "Learn programming and domain fundamentals",
                "year_2": "Learn advanced topics and tools",
                "year_3": "Build projects and internships",
                "year_4": "Specialize in a domain",
            },
        )
    elif stream:
        stream_norm = stream.replace(" ", "_")
        learning_roadmap = STREAM_ROADMAP.get(
            stream_norm,
            {
                "year_1": "Build strong foundations in core subjects",
                "year_2": "Explore advanced topics and electives",
                "year_3": "Gain practical experience and projects",
                "year_4": "Specialize and prepare for career entry",
            },
        )
    else:
        learning_roadmap = {
            "year_1": "Build strong foundations in core subjects",
            "year_2": "Explore advanced topics and electives",
            "year_3": "Gain practical experience and projects",
            "year_4": "Specialize and prepare for career entry",
        }

    # Build future_roles
    if branch:
        branch_norm = branch.replace(" ", "_")
        future_roles = BRANCH_FUTURE_ROLES.get(
            branch_norm,
            ["software engineer", "data scientist", "analyst"],
        )
    elif stream:
        stream_lower = stream.replace(" ", "_")
        if stream_lower == "science":
            future_roles = ["software engineer", "data scientist", "engineer", "researcher"]
        elif stream_lower == "commerce":
            future_roles = ["analyst", "manager", "consultant", "entrepreneur"]
        elif stream_lower == "arts":
            future_roles = ["designer", "writer", "researcher", "consultant"]
        else:
            future_roles = ["technician", "specialist", "engineer"]
    else:
        future_roles = ["software engineer", "data scientist", "analyst"]

    return {
        "reasoning": reasoning,
        "skills_to_develop": skills_to_develop,
        "learning_roadmap": learning_roadmap,
        "future_roles": future_roles,
    }
