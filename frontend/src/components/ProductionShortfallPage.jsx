import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "../api";
import ForecastTool from "./ForecastTool";

function downloadReport(summary) {
  const blob = new Blob([summary], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "manganese_exploration_report.txt";
  a.click();
  URL.revokeObjectURL(url);
}

export default function ProductionShortfallPage({ mines, zones }) {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const activeMines = mines.filter((m) => m.status === "active");
    Promise.all(activeMines.map((m) => api.getProduction(m.id)))
      .then((allProd) => {
        const rows = activeMines.map((m, i) => {
          const prod = allProd[i];
          const last = prod[prod.length - 1];
          if (!last) return null;
          const current = last.actual_tonnes / 1000; // to kilotonnes for compact display
          const required = last.planned_tonnes / 1000;
          const gap = Math.max(0, required - current);
          return { zone: m.name.replace(" Manganese Block", "").replace(" Manganese Mine", ""), current: +current.toFixed(1), required: +required.toFixed(1), gap: +gap.toFixed(1) };
        }).filter(Boolean);
        setChartData(rows);
        setLoading(false);
      });
  }, [mines]);

  const topZones = zones
    ? [...zones.features]
        .sort((a, b) => b.properties.prospectivity_score - a.properties.prospectivity_score)
        .slice(0, 5)
        .map((f) => ({
          zone: f.properties.id,
          reserve: ((f.properties.reserve_min + f.properties.reserve_max) / 2 / 1000).toFixed(2),
          confidence: Math.round(f.properties.confidence * 100),
        }))
    : [];

  const totalGap = chartData.reduce((s, r) => s + r.gap, 0);
  const totalRequired = chartData.reduce((s, r) => s + r.required, 0);
  const coveragePct = totalRequired ? Math.round(((totalRequired - totalGap) / totalRequired) * 100) : 0;

  function handleGenerateReport() {
    const lines = [
      "MANGANESE PRODUCTION SHORTFALL REPORT",
      "SIH26009 Manganese Intelligence Platform",
      "=".repeat(50),
      "",
      "PRODUCTION SHORTFALL BY ZONE (kilotonnes)",
      ...chartData.map((r) => `  ${r.zone}: Current ${r.current} | Required ${r.required} | Gap ${r.gap}`),
      "",
      "TOP POTENTIAL ZONES (from the prospectivity model)",
      ...topZones.map((z) => `  ${z.zone}: Est. reserve ${z.reserve} kt, confidence ${z.confidence}%`),
      "",
      `Overall coverage: ${coveragePct}% of required production currently met.`,
      "",
      "NOTE: This report is generated from mock/synthetic demonstration data",
      "calibrated against real IBM Yearbook statistics. See docs/methodology.md",
      "for full data provenance.",
    ];
    downloadReport(lines.join("\n"));
  }

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <ForecastTool />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20 }}>
        <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20 }}>
          <h3 style={{ fontSize: 15, marginBottom: 4 }}>Production Shortfall Analysis</h3>
          <p style={{ color: "var(--text-soft)", fontSize: 12, marginBottom: 16 }}>Production (kilotonnes) by zone</p>
          {loading ? (
            <p style={{ color: "var(--text-soft)" }}>Loading…</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="zone" tick={{ fontSize: 11, fill: "var(--text-soft)" }} />
                <YAxis tick={{ fontSize: 12, fill: "var(--text-soft)" }} />
                <Tooltip contentStyle={{ background: "white", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="current" name="Current" fill="var(--primary-blue)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="required" name="Required" fill="var(--accent-green)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="gap" name="Gap" fill="var(--danger-red)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, textAlign: "center" }}>
            <div style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 8 }}>Potential Contribution</div>
            <div style={{ fontFamily: "var(--font)", fontSize: 40, fontWeight: 700, color: "var(--accent-green)" }}>{coveragePct}%</div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>of required production currently met</div>
          </div>

          <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20 }}>
            <h4 style={{ fontSize: 13, marginBottom: 8 }}>Generate Exploration Report</h4>
            <p style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 14 }}>
              Download a text summary with shortfall figures and top potential zones.
            </p>
            <button
              onClick={handleGenerateReport}
              style={{ background: "linear-gradient(135deg, #2563EB, #1D4ED8)", color: "white", padding: "11px 16px", boxShadow: "0 2px 8px rgba(37,99,235,0.35)", fontWeight: 600, fontSize: 13, width: "100%" }}
            >
              Generate Report
            </button>
          </div>
        </div>
      </div>

      <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, marginTop: 20 }}>
        <h3 style={{ fontSize: 15, marginBottom: 14 }}>Top Potential Zones</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--text-soft)", fontSize: 12 }}>
              <th style={{ padding: "8px 4px", borderBottom: "1px solid var(--border)" }}>Zone</th>
              <th style={{ padding: "8px 4px", borderBottom: "1px solid var(--border)" }}>Est. Reserve (kt)</th>
              <th style={{ padding: "8px 4px", borderBottom: "1px solid var(--border)" }}>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {topZones.map((z) => (
              <tr key={z.zone}>
                <td style={{ padding: "8px 4px", borderBottom: "1px solid var(--border)" }}>{z.zone}</td>
                <td style={{ padding: "8px 4px", borderBottom: "1px solid var(--border)" }}>{z.reserve}</td>
                <td style={{ padding: "8px 4px", borderBottom: "1px solid var(--border)", color: "var(--accent-green)" }}>{z.confidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}
