import SalaryChart from "./SalaryChart";
import DemandTrendChart from "./DemandTrendChart";

export default function SimulationDashboard({ simulation }) {
  const paths = simulation.generatedPaths || [];

  if (paths.length === 0) {
    return <p>No simulation results yet.</p>;
  }

  return (
    <div className="dashboard">
      <h2>Simulation Results</h2>
      {paths.map((path) => {
        const latest = path.averageCase[path.averageCase.length - 1];
        return (
          <section key={path.pathName} className="card">
            <div className="stats-row">
              <div>
                <h3>{path.pathName}</h3>
                <p>Final Average Salary: {latest.salary.toLocaleString()}</p>
                <p>Final Stability: {latest.stabilityScore}</p>
                <p>Final Burnout Risk: {latest.burnoutRisk}</p>
              </div>
              <div>
                <h4>Switch if stagnates</h4>
                <ul>
                  {path.switchOptions.map((option) => (
                    <li key={option}>{option}</li>
                  ))}
                </ul>
              </div>
            </div>
            <SalaryChart path={path} />
            <DemandTrendChart path={path} />
          </section>
        );
      })}
    </div>
  );
}
