from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass
class ScenarioMultipliers:
    salary: float
    stability: float
    burnout: float


SCENARIO = {
    "best": ScenarioMultipliers(salary=1.12, stability=1.08, burnout=0.90),
    "average": ScenarioMultipliers(salary=1.00, stability=1.00, burnout=1.00),
    "worst": ScenarioMultipliers(salary=0.88, stability=0.90, burnout=1.12),
}


def demand_label_from_score(score: float) -> str:
    if score >= 0.66:
        return "increasing"
    if score >= 0.40:
        return "stable"
    return "declining"


def project_path(
    path_name: str,
    base_salary: float,
    demand_score: float,
    transition_prob: float,
    burnout_score: float,
    years: int,
) -> Dict:
    yearly_growth = 0.04 + (demand_score * 0.07) + (transition_prob * 0.03)
    yearly_growth = min(0.18, max(0.01, yearly_growth))

    base_stability = min(100.0, max(20.0, 55 + (demand_score * 30) - (burnout_score * 20)))
    base_burnout = min(100.0, max(5.0, burnout_score * 100))

    output = {"pathName": path_name, "bestCase": [], "averageCase": [], "worstCase": [], "switchOptions": []}

    for scenario_name, m in SCENARIO.items():
        projections: List[Dict] = []
        current_salary = base_salary * m.salary
        for year in range(1, years + 1):
            demand_adjusted = min(1.0, max(0.0, demand_score + np.random.normal(0, 0.03)))
            demand_trend = demand_label_from_score(demand_adjusted)

            current_salary = current_salary * (1 + yearly_growth * (1 + (year / 100)))
            stability = min(100.0, max(0.0, base_stability * m.stability - (year * 0.8)))
            burnout = min(100.0, max(0.0, base_burnout * m.burnout + (year * 1.4)))

            projections.append(
                {
                    "year": year,
                    "salary": round(float(current_salary), 2),
                    "demandTrend": demand_trend,
                    "stabilityScore": round(float(stability), 2),
                    "burnoutRisk": round(float(burnout), 2),
                }
            )

        output[f"{scenario_name}Case"] = projections

    # Higher switch probability when demand and stability are weak.
    if demand_score < 0.45 or base_stability < 60:
        output["switchOptions"] = [
            "data_analyst",
            "product_analyst",
            "solution_consultant",
        ]
    else:
        output["switchOptions"] = ["technical_lead", "domain_specialist"]

    return output
