const LEVEL_COLOR = { High: "var(--danger-red)", Medium: "var(--warning-orange)", Low: "var(--accent-green)" };
const LEVEL_BG = { High: "var(--danger-red-soft)", Medium: "var(--warning-orange-soft)", Low: "var(--accent-green-soft)" };

export default function RiskPanel({ risk, recommendation, forecast }) {
  if (!risk) return <p style={{ color: "var(--text-soft)" }}>No risk data for this mine.</p>;

  return (
    <div>
      {forecast && forecast.length > 0 && (
        <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          {forecast.map((f) => (
            <div key={f.period} style={{
              background: LEVEL_BG[f.risk_level], borderRadius: 10, padding: "12px 16px", minWidth: 120,
            }}>
              <div style={{ fontSize: 11, color: "var(--text-soft)" }}>{f.period}</div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{f.shortfall_pct}% short</div>
              <div style={{ color: LEVEL_COLOR[f.risk_level], fontWeight: 600, fontSize: 12 }}>{f.risk_level} risk</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginBottom: 16 }}>
        {risk.factors.map((f) => (
          <div key={f.name} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
              <span>{f.name}</span>
              <span style={{ color: "var(--text-soft)" }}>{f.weight_pct}%</span>
            </div>
            <div style={{ background: "var(--border)", borderRadius: 4, height: 8, overflow: "hidden" }}>
              <div style={{
                width: `${f.value * 100}%`, height: "100%",
                background: f.value > 0.5 ? "var(--danger-red)" : f.value > 0.3 ? "var(--warning-orange)" : "var(--accent-green)",
              }} />
            </div>
          </div>
        ))}
      </div>

      {recommendation && (
        <div style={{
          background: "var(--accent-green-soft)", borderLeft: "3px solid var(--accent-green)",
          borderRadius: 6, padding: "10px 14px", fontSize: 13,
        }}>
          <strong>Recommended action:</strong> {recommendation.recommendation}
        </div>
      )}
    </div>
  );
}
