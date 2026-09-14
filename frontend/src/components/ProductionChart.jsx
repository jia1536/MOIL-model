import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";

export default function ProductionChart({ data }) {
  if (!data || data.length === 0) {
    return <p style={{ color: "var(--text-soft)" }}>No production history for this mine.</p>;
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="period" tick={{ fontSize: 12, fill: "var(--text-soft)" }} />
        <YAxis tick={{ fontSize: 12, fill: "var(--text-soft)" }} />
        <Tooltip contentStyle={{ background: "white", border: "1px solid var(--border)", borderRadius: 8 }} />
        <Legend wrapperStyle={{ fontSize: 13 }} />
        <Bar dataKey="planned_tonnes" name="Planned" fill="#BFDBFE" radius={[4, 4, 0, 0]} />
        <Bar dataKey="actual_tonnes" name="Actual" fill="var(--primary-blue)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
