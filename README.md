# AI Career Simulator MVP

End-to-end MVP that predicts and simulates career outcomes over 5-10 years using explainable ML + heuristics.

## 1) System Architecture

### High-level flow

1. User submits profile via React dashboard.
2. Node.js/Express API validates input and stores simulation records in MongoDB.
3. Express calls Python ML service (`/simulate-career`) for predictions.
4. Python service:
   - transforms profile to model features,
   - predicts salary, demand confidence, transition probability, burnout probability,
   - runs multi-path year-by-year simulation for best/average/worst scenarios.
5. Express returns full simulation JSON to frontend for charts.

### Tech Stack

- Backend API: Node.js + Express + Mongoose
- Database: MongoDB
- ML service: FastAPI + scikit-learn + pandas + numpy
- Frontend: React + Vite + Recharts

### Why this architecture

- **Separation of concerns**: Node handles auth/session/business API concerns; Python handles data science tooling.
- **Fast iteration**: ML model can be retrained/deployed independently of API/frontend.
- **Explainability first**: classic models (RF, logistic regression) are easier to explain to universities/investors than deep black-box stacks.

---

## 2) Folder Structure

```text
ai-career-simulator/
├─ backend/
│  ├─ package.json
│  ├─ .env.example
│  └─ src/
│     ├─ config/db.js
│     ├─ models/Simulation.js
│     ├─ routes/simulationRoutes.js
│     ├─ services/mlClient.js
│     ├─ services/simulationService.js
│     └─ server.js
├─ ml-service/
│  ├─ requirements.txt
│  ├─ train.py
│  ├─ app.py
│  ├─ simulation.py
│  ├─ artifacts/                # generated after training
│  ├─ data/
│  │  └─ README.md
│  └─ utils/preprocess.py
├─ frontend/
│  ├─ package.json
│  ├─ index.html
│  ├─ vite.config.js
│  └─ src/
│     ├─ main.jsx
│     ├─ App.jsx
│     ├─ api.js
│     ├─ styles.css
│     └─ components/
│        ├─ UserInputForm.jsx
│        ├─ SimulationDashboard.jsx
│        ├─ SalaryChart.jsx
│        └─ DemandTrendChart.jsx
└─ README.md
```

---

## 3) Datasets and Feature Mapping

Use free/open CSV datasets (Kaggle/GitHub/public labor reports), then merge them into `ml-service/data/career_training_data.csv`.

### Dataset list

1. Job postings + descriptions
2. Salary datasets (India + global)
3. Skills demand dataset (time-based demand index)
4. Career trajectory / transitions dataset
5. Burnout proxy data (hours, attrition, stress surveys)

### Mapping to features

- `education_level`, `degree_stream` -> baseline qualification signal
- `skills` -> capability and role-fit vector (multi-hot encoded)
- `location` -> salary and demand regional multiplier proxy
- `risk_preference` -> affects scenario weights and transition bias
- `years_experience` -> salary progression stage
- `demand_label` -> supervision target for demand trend model
- `next_role_success` -> target for transition probability model
- `burnout_label` (+ burnout proxies during data prep) -> burnout model target

### Handling noisy/incomplete data

- text normalization (lowercase, trim, fill unknown)
- median imputation for numeric gaps
- unknown category handling via `OneHotEncoder(handle_unknown="ignore")`
- skills/interests parsed from comma-separated strings

---

## 4) ML Pipeline (Training + Serving)

## 4.1 Preprocessing

Implemented in `ml-service/utils/preprocess.py`:

- Clean text fields and missing values.
- Parse `skills` and `interests` into token arrays.
- Build feature matrix:
  - categorical features -> one-hot encoding,
  - numeric features -> scaling,
  - multi-label skills/interests -> binary vectors.

## 4.2 Models

Implemented in `ml-service/train.py`:

- Salary prediction: `RandomForestRegressor`
- Demand trend classification: `RandomForestClassifier`
- Transition probability: `LogisticRegression`
- Burnout risk: `LogisticRegression` (hybrid with simulation heuristics)

Artifacts saved into `ml-service/artifacts/` using `joblib`.

## 4.3 Prediction Service

Implemented in `ml-service/app.py`:

- Endpoint: `POST /simulate-career`
- Loads model artifacts
- Generates base predictions:
  - `base_salary`
  - `demand_score` (class confidence proxy)
  - `transition_prob`
  - `burnout_prob`
- Runs year-wise simulation (`ml-service/simulation.py`) over multiple paths and scenarios.

---

## 5) Simulation Computation Logic

For each path:

1. Start with base salary from regression model.
2. Compute yearly growth using:
   - demand score,
   - transition probability,
   - bounded growth constraints (1%-18%).
3. Simulate each year:
   - projected salary,
   - demand trend (`increasing/stable/declining`),
   - career stability score,
   - burnout risk score.
4. Build three scenarios:
   - best-case (higher salary/stability, lower burnout),
   - average-case,
   - worst-case (lower salary/stability, higher burnout).
5. Suggest switch options when demand/stability weakens.

### Why this is realistic for MVP

- Uses learned signal from real-world data where possible.
- Uses transparent heuristic bounds for uncertain long-term forecasts.
- Avoids fragile black-box sequence models for limited/noisy startup datasets.

---

## 6) Backend API Routes

Base URL: `http://localhost:4000/api`

- `POST /simulate`
  - accepts user profile
  - calls ML service
  - persists result in MongoDB
  - returns simulation object
- `GET /simulations`
  - returns recent simulation history (latest 20)
- `GET /simulations/:id`
  - returns single simulation by ID

Health endpoint:

- `GET /health` on backend (`:4000`)
- `GET /health` on ML service (`:8000`)

---

## 7) Sample MongoDB Schema

Stored via `backend/src/models/Simulation.js`:

- `inputProfile`
  - education, degree stream, skills, location, interests, risk, years
- `generatedPaths[]`
  - `pathName`
  - `bestCase[]`, `averageCase[]`, `worstCase[]`
    - `year`, `salary`, `demandTrend`, `stabilityScore`, `burnoutRisk`
  - `switchOptions[]`
- `modelMetadata`
  - model versions per sub-model

---

## 8) Frontend Dashboard

React components:

- `UserInputForm`: collects all required profile fields.
- `SimulationDashboard`: renders each career path and KPI snapshot.
- `SalaryChart`: line chart for best/average/worst salary curves.
- `DemandTrendChart`: bar chart for demand trend by year.

WHY chart choices:

- salary projections are best understood as trend lines over time,
- demand trend is categorical ordinal, easy to scan as bars by year.

---

## 9) Example API Request/Response

### `POST /api/simulate` request

```json
{
  "educationLevel": "bachelors",
  "degreeStream": "computer science",
  "skills": ["python", "sql", "machine learning"],
  "location": "india",
  "interests": ["analytics", "product"],
  "riskPreference": "medium",
  "yearsToSimulate": 10
}
```

### Example response (truncated)

```json
{
  "_id": "66de1a88dcb98f3c2dd018a4",
  "inputProfile": {
    "educationLevel": "bachelors",
    "degreeStream": "computer science",
    "skills": ["python", "sql", "machine learning"],
    "location": "india",
    "interests": ["analytics", "product"],
    "riskPreference": "medium",
    "yearsToSimulate": 10
  },
  "generatedPaths": [
    {
      "pathName": "software_engineer",
      "bestCase": [
        {
          "year": 1,
          "salary": 1142000.22,
          "demandTrend": "increasing",
          "stabilityScore": 86.4,
          "burnoutRisk": 28.2
        }
      ],
      "averageCase": [
        {
          "year": 1,
          "salary": 1023000.1,
          "demandTrend": "stable",
          "stabilityScore": 80.0,
          "burnoutRisk": 31.3
        }
      ],
      "worstCase": [
        {
          "year": 1,
          "salary": 907800.75,
          "demandTrend": "stable",
          "stabilityScore": 71.2,
          "burnoutRisk": 35.8
        }
      ],
      "switchOptions": ["technical_lead", "domain_specialist"]
    }
  ],
  "modelMetadata": {
    "salaryModelVersion": "rf_v1",
    "demandModelVersion": "rf_classifier_v1",
    "transitionModelVersion": "logreg_v1",
    "burnoutModelVersion": "hybrid_logreg_v1"
  },
  "createdAt": "2026-02-28T09:20:12.000Z"
}
```

---

## 10) Setup Instructions (README style)

## Prerequisites

- Node.js 18+
- Python 3.10+
- MongoDB local instance

## Step A: ML service

```bash
cd ml-service
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train.py
uvicorn app:app --reload --port 8000
```

## Step B: Backend API

```bash
cd backend
cp .env.example .env
npm install
npm run dev
```

## Step C: Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:5173`

---

## 11) Assumptions and Limitations

- Long-term salary prediction beyond 5-10 years has high uncertainty.
- MVP treats merged CSV as single source (not full production ETL).
- Demand trend is simplified classification confidence, not full macroeconomic forecasting.
- Burnout estimation combines model output with heuristic progression.
- No identity/auth layer in MVP.

---

## 12) Next Production Upgrades

- scheduled ETL jobs + data versioning
- confidence intervals and scenario explainability cards
- cohort-specific benchmarking (college tier, sector, city)`
- model monitoring (drift, re-training cadence, fairness checks)
- optional graph database for richer transition graph traversal

