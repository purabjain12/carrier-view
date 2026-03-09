import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

export default function SalaryChart({ path }) {
  const points = path.averageCase.map((avgYear, idx) => ({
    year: avgYear.year,
    best: path.bestCase[idx].salary,
    average: avgYear.salary,
    worst: path.worstCase[idx].salary
  }));

  return (
    <div className="chart-card">
      <h3>{path.pathName} - Salary Projection</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={points}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="best" stroke="#16a34a" />
          <Line type="monotone" dataKey="average" stroke="#2563eb" />
          <Line type="monotone" dataKey="worst" stroke="#dc2626" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
