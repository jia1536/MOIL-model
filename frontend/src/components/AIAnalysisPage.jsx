import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { api } from "../api";

const LEVEL_COLOR = {
  "very high": "var(--danger-red)",
  high: "var(--danger-red)",
  medium: "var(--warning-orange)",
  low: "var(--accent-green)",
  "very low": "var(--accent-green)",
};

export default function AIAnalysisPage({ selectedMine, mines = [] }) {
  const [lat, setLat] = useState(selectedMine?.lat || 21.8);
  const [lng, setLng] = useState(selectedMine?.lng || 80.18);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runAnalysis() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.predictPoint(lat, lng);
      setResult(res);
    } catch (e) {
      setError(e.message || "Could not reach the prediction API. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  function pickMine(e) {
    const m = mines.find((x) => String(x.id) === e.target.value);
    if (m) { setLat(m.lat); setLng(m.lng); }
  }

  const featureChartData = (result?.top_features || [])
    .map((f) => ({ name: f.name, contribution: f.contribution }))
    .sort((a, b) => b.contribution - a.contribution);

  return (
    <div>
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 15, marginBottom: 4 }}>Prospectivity Analysis</h3>
        <p style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 16 }}>
          Runs the live pipeline (satellite, geology, terrain, model, viability) for a coordinate. This is
          the same v3 pipeline used by the Map tab's point inspector.
        </p>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 14 }}>
          <label style={{ fontSize: 11, color: "var(--text-soft)" }}>
            Latitude
            <input
              type="number" step="any" value={lat}
              onChange={(e) => setLat(parseFloat(e.target.value))}
              style={{ display: "block", width: 140, marginTop: 3, padding: "6px 8px", background: "var(--page-bg)", color: "var(--text)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13 }}
            />
          </label>
          <label style={{ fontSize: 11, color: "var(--text-soft)" }}>
            Longitude
            <input
              type="number" step="any" value={lng}
              onChange={(e) => setLng(parseFloat(e.target.value))}
              style={{ display: "block", width: 140, marginTop: 3, padding: "6px 8px", background: "var(--page-bg)", color: "var(--text)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13 }}
            />
          </label>
          {mines.length > 0 && (
            <label style={{ fontSize: 11, color: "var(--text-soft)" }}>
              Or pick a known mine
              <select
                defaultValue=""
                onChange={pickMine}
                style={{ display: "block", width: 220, marginTop: 3, padding: "6px 8px", background: "var(--page-bg)", color: "var(--text)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13 }}
              >
                <option value="" disabled>Select a mine…</option>
                {mines.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            </label>
          )}
          <button
            onClick={runAnalysis}
            disabled={loading}
            style={{ background: "linear-gradient(135deg, #2563EB, #1D4ED8)", color: "white", padding: "11px 22px", boxShadow: "0 2px 8px rgba(37,99,235,0.35)", fontWeight: 600, fontSize: 13 }}
          >
            {loading ? "Running analysis…" : "Run analysis"}
          </button>
        </div>

        {error && <p style={{ color: "var(--danger-red)", fontSize: 13 }}>{error}</p>}
      </div>

      {result && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.3fr", gap: 20 }}>
          <div className="card">
            <h4 style={{ fontSize: 13, marginBottom: 12 }}>Prospectivity</h4>
            <div style={{
              display: "inline-block", padding: "3px 10px", borderRadius: 6, marginBottom: 10,
              background: LEVEL_COLOR[result.level] || "var(--border)", color: "white", fontSize: 12, fontWeight: 600,
            }}>
              {result.level}
            </div>
            <div style={{ fontFamily: "var(--font)", fontSize: 32, fontWeight: 700, marginBottom: 4 }}>
              {result.prospectivity.prospectivity_score}
            </div>
            <div style={{ fontSize: 11, color: "var(--text-soft)", marginBottom: 16 }}>prospectivity score</div>

            <h4 style={{ fontSize: 13, marginBottom: 6 }}>Confidence for this point</h4>
            <div style={{ background: "var(--border)", borderRadius: 4, height: 8, overflow: "hidden", marginBottom: 4 }}>
              <div style={{ width: `${result.prospectivity.confidence * 100}%`, height: "100%", background: "var(--primary-blue)" }} />
            </div>
            <div style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 12 }}>{Math.round(result.prospectivity.confidence * 100)}% agreement across the model's 250 trees</div>

            <h4 style={{ fontSize: 13, marginBottom: 4 }}>Overall model skill (R²)</h4>
            <div style={{ fontSize: 13 }}>{result.prospectivity.model_r2}</div>
          </div>

          <div className="card">
            <h4 style={{ fontSize: 13, marginBottom: 12 }}>Reserves and viability</h4>
            <div style={{ fontFamily: "var(--font)", fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
              {result.prospectivity.reserve_min_tonnes?.toLocaleString?.()} – {result.prospectivity.reserve_max_tonnes?.toLocaleString?.()} t
            </div>
            <div style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 16 }}>Estimated manganese reserve range</div>

            <h4 style={{ fontSize: 13, marginBottom: 6 }}>Viability index</h4>
            <div style={{ fontFamily: "var(--font)", fontSize: 24, fontWeight: 700, marginBottom: 10 }}>
              {result.viability?.viability_index}
            </div>

            <h4 style={{ fontSize: 13, marginBottom: 4 }}>Nearest known mine</h4>
            <div style={{ fontSize: 13, marginBottom: 10 }}>{result.nearest_mine}</div>

            {result.forecast && (
              <>
                <h4 style={{ fontSize: 13, marginBottom: 4 }}>Production shortfall risk</h4>
                <div style={{ fontSize: 13 }}>{result.forecast.risk_level}</div>
              </>
            )}
          </div>

          <div className="card">
            <h4 style={{ fontSize: 13, marginBottom: 12 }}>Top contributing features</h4>
            {featureChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={featureChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "white", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
                    {featureChartData.map((f, i) => (
                      <Cell key={i} fill={f.contribution >= 0 ? "var(--accent-green)" : "var(--danger-red)"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p style={{ fontSize: 12, color: "var(--text-soft)" }}>No feature breakdown returned.</p>
            )}
            <p style={{ fontSize: 10, color: "var(--text-soft)", marginTop: 8 }}>
              Per-point perturbation-based explanation from the live model, computed for this exact coordinate.
            </p>
          </div>

          <div className="card" style={{ gridColumn: "1 / -1" }}>
            <h4 style={{ fontSize: 13, marginBottom: 12 }}>Site attributes</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
              <Stat label="Thickness (illustrative)" value={result.thickness ? `${result.thickness.thickness_m} m` : "-"} />
              <Stat label="Water table depth (illustrative)" value={result.water_table ? `${result.water_table.water_table_depth_m} m` : "-"} />
              <Stat label="Social infrastructure score" value={result.social_infra?.social_infra_score ?? "-"} />
              <Stat label="Known operators nearby" value={result.companies?.length > 0 ? result.companies.join(", ") : "None on record"} />
            </div>
            <p style={{ fontSize: 10, color: "var(--text-soft)", marginTop: 12 }}>
              Thickness, water table and per-point social infrastructure score are illustrative estimates
              calibrated to real state and geology averages, not direct borehole or CGWB measurements.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: "var(--text-soft)" }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
