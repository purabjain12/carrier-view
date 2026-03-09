import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

function trendToValue(trend) {
  if (trend === "increasing") return 3;
  if (trend === "stable") return 2;
  return 1;
}

export default function DemandTrendChart({ path }) {
  const data = path.averageCase.map((item) => ({
    year: item.year,
    demandValue: trendToValue(item.demandTrend),
    demandTrend: item.demandTrend
  }));

  return (
    <div className="chart-card">
      <h3>{path.pathName} - Demand Trend</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis ticks={[1, 2, 3]} domain={[0, 3]} />
          <Tooltip />
          <Bar dataKey="demandValue" fill="#0ea5e9" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
