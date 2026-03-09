import { useState } from "react";
import UserInputForm from "./components/UserInputForm";
import SimulationDashboard from "./components/SimulationDashboard";
import { simulateCareer } from "./api";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [simulation, setSimulation] = useState(null);

  async function handleSubmit(payload) {
    setError("");
    setLoading(true);
    try {
      const result = await simulateCareer(payload);
      setSimulation(result);
    } catch (e) {
      setError(e.message || "Failed to simulate");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>AI Career Simulator</h1>
      <p className="subtitle">
        Predict salary, demand, stability, burnout, and career switches across 5-10 years.
      </p>
      <UserInputForm onSubmit={handleSubmit} loading={loading} />
      {error && <p className="error">{error}</p>}
      {simulation && <SimulationDashboard simulation={simulation} />}
    </main>
  );
}
