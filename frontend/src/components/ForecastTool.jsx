import { useState } from "react";
import { api } from "../api";

const LEVEL_BADGE = {
  High: { bg: "var(--danger-red-soft)", color: "var(--danger-red)" },
  Medium: { bg: "var(--warning-orange-soft)", color: "var(--warning-orange)" },
  Low: { bg: "var(--accent-green-soft)", color: "var(--accent-green)" },
};

const DEFAULTS = {
  mine_type: "underground",
  historical_avg: 10000,
  planned_tonnes: 12000,
  downtime_hours: 120,
  rainfall: 1200,
};

export default function ForecastTool() {
  const [form, setForm] = useState(DEFAULTS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function runPrediction() {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        mine_type: form.mine_type,
        historical_avg: parseFloat(form.historical_avg),
        planned_tonnes: parseFloat(form.planned_tonnes),
        downtime_hours: parseFloat(form.downtime_hours),
        rainfall: parseFloat(form.rainfall),
      };
      const res = await api.predictForecast(payload);
      setResult(res);
    } catch (e) {
      setError("Could not reach the prediction API. Is the backend running on port 8000?");
    } finally {
      setLoading(false);
    }
  }

  const badge = result ? (LEVEL_BADGE[result.risk_level] || LEVEL_BADGE.Medium) : null;

  return (
    <div className="card">
      <h3 style={{ fontSize: 15, marginBottom: 4 }}>Live Shortfall Prediction</h3>
      <p style={{ color: "var(--text-soft)", fontSize: 13, marginBottom: 18 }}>
        Enter mine conditions to get a real-time forecast from the trained model (not mock data).
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12, marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: "var(--text-soft)" }}>
          Mine type
          <select
            value={form.mine_type}
            onChange={(e) => update("mine_type", e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 4, padding: "7px 8px", border: "1px solid var(--border)", borderRadius: 6, fontSize: 14, background: "white", color: "var(--text)" }}
          >
            <option value="underground">Underground</option>
            <option value="opencast">Opencast</option>
          </select>
        </label>
        <label style={{ fontSize: 12, color: "var(--text-soft)" }}>
          Historical avg (tonnes)
          <input type="number" value={form.historical_avg} onChange={(e) => update("historical_avg", e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 4, padding: "7px 8px", border: "1px solid var(--border)", borderRadius: 6, fontSize: 14 }} />
        </label>
        <label style={{ fontSize: 12, color: "var(--text-soft)" }}>
          Planned tonnes
          <input type="number" value={form.planned_tonnes} onChange={(e) => update("planned_tonnes", e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 4, padding: "7px 8px", border: "1px solid var(--border)", borderRadius: 6, fontSize: 14 }} />
        </label>
        <label style={{ fontSize: 12, color: "var(--text-soft)" }}>
          Downtime hours
          <input type="number" value={form.downtime_hours} onChange={(e) => update("downtime_hours", e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 4, padding: "7px 8px", border: "1px solid var(--border)", borderRadius: 6, fontSize: 14 }} />
        </label>
        <label style={{ fontSize: 12, color: "var(--text-soft)" }}>
          Rainfall (mm)
          <input type="number" value={form.rainfall} onChange={(e) => update("rainfall", e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 4, padding: "7px 8px", border: "1px solid var(--border)", borderRadius: 6, fontSize: 14 }} />
        </label>
      </div>

      <button
        onClick={runPrediction}
        disabled={loading}
        style={{ background: "linear-gradient(135deg, #2563EB, #1D4ED8)", color: "white", padding: "11px 22px", boxShadow: "0 2px 8px rgba(37,99,235,0.35)", fontSize: 14, fontWeight: 600 }}
      >
        {loading ? "Predicting…" : "Run prediction"}
      </button>

      {error && <p style={{ color: "var(--danger-red)", marginTop: 12, fontSize: 13 }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 20, display: "flex", gap: 24, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>Forecast tonnes</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{result.forecast_tonnes.toLocaleString()}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>Shortfall</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--danger-red)" }}>{result.shortfall_pct}%</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>Risk score</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{result.risk_score}</div>
          </div>
          <span style={{ background: badge.bg, color: badge.color, fontSize: 13, fontWeight: 600, padding: "6px 14px", borderRadius: 8 }}>
            {result.risk_level} risk
          </span>
        </div>
      )}
    </div>
  );
}
