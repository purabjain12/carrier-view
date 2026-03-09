import { useState } from "react";

const EDUCATION_OPTIONS = ["bachelors", "masters", "phd", "diploma"];
const DEGREE_OPTIONS = [
  { label: "Computer Science / IT", value: "computer_science" },
  { label: "Engineering (Non-CS)", value: "engineering" },
  { label: "Business / Management", value: "business" },
  { label: "Science / Math / Stats", value: "science_math_stats" },
  { label: "Arts / Humanities", value: "arts_humanities" },
  { label: "Other", value: "other" }
];
const LOCATION_OPTIONS = ["india", "usa", "uk", "canada", "germany", "singapore"];
const SKILL_OPTIONS = [
  "python",
  "sql",
  "excel",
  "java",
  "machine learning",
  "communication",
  "product thinking",
  "analytics",
  "tableau",
  "statistics"
];
const INTEREST_OPTIONS = [
  "coding",
  "problem_solving",
  "research",
  "management",
  "design",
  "data_analysis"
];

const initialState = {
  educationLevel: "bachelors",
  degreeStream: "computer_science",
  skills: ["python", "sql", "excel"],
  location: "india",
  interests: ["data_analysis"],
  riskPreference: "medium",
  yearsToSimulate: 5
};

export default function UserInputForm({ onSubmit, loading }) {
  const [form, setForm] = useState(initialState);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function toggleMulti(name, value, maxAllowed) {
    setForm((prev) => {
      const selected = prev[name];
      const exists = selected.includes(value);
      if (exists) {
        return { ...prev, [name]: selected.filter((item) => item !== value) };
      }
      if (selected.length >= maxAllowed) {
        return prev;
      }
      return { ...prev, [name]: [...selected, value] };
    });
  }

  function submit(e) {
    e.preventDefault();
    if (form.skills.length < 2) {
      return;
    }
    onSubmit({
      ...form,
      yearsToSimulate: Number(form.yearsToSimulate)
    });
  }

  return (
    <form className="card form-grid" onSubmit={submit}>
      <h2>Career Inputs</h2>
      <label>
        Education Level
        <select name="educationLevel" value={form.educationLevel} onChange={handleChange}>
          {EDUCATION_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label>
        Degree / Stream
        <select name="degreeStream" value={form.degreeStream} onChange={handleChange}>
          {DEGREE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Location
        <select name="location" value={form.location} onChange={handleChange}>
          {LOCATION_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label className="full-width">
        Skills (select 2 to 8)
        <div className="chip-group">
          {SKILL_OPTIONS.map((skill) => (
            <button
              key={skill}
              type="button"
              className={`chip ${form.skills.includes(skill) ? "chip-selected" : ""}`}
              onClick={() => toggleMulti("skills", skill, 8)}
            >
              {skill}
            </button>
          ))}
        </div>
        <small>{form.skills.length} selected</small>
      </label>
      <label className="full-width">
        Interests (optional, max 3)
        <div className="chip-group">
          {INTEREST_OPTIONS.map((interest) => (
            <button
              key={interest}
              type="button"
              className={`chip ${form.interests.includes(interest) ? "chip-selected" : ""}`}
              onClick={() => toggleMulti("interests", interest, 3)}
            >
              {interest}
            </button>
          ))}
        </div>
      </label>
      <label>
        Risk Preference
        <select name="riskPreference" value={form.riskPreference} onChange={handleChange}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      <label>
        Years to Simulate
        <input
          name="yearsToSimulate"
          type="number"
          min="5"
          max="10"
          value={form.yearsToSimulate}
          onChange={handleChange}
        />
      </label>
      {form.skills.length < 2 && (
        <p className="error full-width">Select at least 2 skills to continue.</p>
      )}
      <button disabled={loading || form.skills.length < 2} type="submit">
        {loading ? "Running Simulation..." : "Simulate Career"}
      </button>
    </form>
  );
}
