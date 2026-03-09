# Datasets (CSV, free/open sources)

Add CSV files in this folder and create a merged training file:

- `job_postings.csv` (title, location, skills, post_date)
- `salary_data_india_global.csv` (role, location, min_salary, max_salary, median_salary)
- `skills_demand_timeseries.csv` (skill, date, demand_index)
- `career_transitions.csv` (current_role, next_role, success_flag, years_in_role)
- `burnout_proxy.csv` (role, avg_hours, attrition_rate, self_reported_stress)

For MVP training, prepare:

- `career_training_data.csv` with columns:
  - `education_level`
  - `degree_stream`
  - `skills` (comma-separated)
  - `location`
  - `interests` (comma-separated)
  - `risk_preference`
  - `years_experience`
  - `salary`
  - `demand_label` (`increasing` / `stable` / `declining`)
  - `next_role_success` (0/1)
  - `burnout_label` (0/1)
