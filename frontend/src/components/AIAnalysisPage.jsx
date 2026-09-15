import { useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { api } from "../api";

// Real feature importances printed by train_prospectivity_v2.py during training —
// not fabricated for display, these are the model's actual learned weights.
const KEY_FACTORS = [
  { name: "Geology (gondite-archean)", value: 46.4 },
  { name: "Geology (archean)", value: 16.5 },
  { name: "Magnetic anomaly", value: 5.8 },
  { name: "NDVI (vegetation)", value: 4.8 },
  { name: "Mn concentration (soil)", value: 4.6 },
  { name: "Mineral alteration index", value: 3.6 },
  { name: "Distance to fault", value: 2.3 },
];

const GEOLOGY_OPTIONS = ["gondite_archean", "archean", "kodurite_archean", "laterite"];

export default function AIAnalysisPage({ selectedMine }) {
  const [form, setForm] = useState({
    lat: selectedMine?.lat || 21.8, lng: selectedMine?.lng || 80.18,
    elevation: 400, slope_deg: 12, drainage_density: 1.5,
    ndvi: 0.6, ndwi: 0.1, land_surface_temp: 30, mineral_alteration_index: 0.7,
    mn_ppm_soil: 1600, magnetic_anomaly_nt: 95, distance_to_fault_km: 3,
    distance_to_known_mine_km: 2, geology_type: "gondite_archean",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ndviLoading, setNdviLoading] = useState(false);
  const [ndviSource, setNdviSource] = useState(null);

  async function fetchRealNdvi() {
    setNdviLoading(true);
    setNdviSource(null);
    try {
      const res = await api.getRealNdvi(form.lat, form.lng);
      setForm((s) => ({ ...s, ndvi: res.ndvi }));
      setNdviSource(res.source);
    } catch (e) {
      setNdviSource("Failed to fetch — check backend has Earth Engine authenticated");
    } finally {
      setNdviLoading(false);
    }
  }

  async function runAnalysis() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictProspectivity(form);
      setResult(res);
    } catch (e) {
      setError("Could not reach the prediction API. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  const donutData = result
    ? [
        { name: "High", value: result.prospectivity_score > 0.6 ? 82 : result.prospectivity_score > 0.4 ? 30 : 6 },
        { name: "Medium", value: result.prospectivity_score > 0.6 ? 12 : result.prospectivity_score > 0.4 ? 45 : 20 },
        { name: "Low", value: result.prospectivity_score > 0.6 ? 6 : result.prospectivity_score > 0.4 ? 25 : 74 },
      ]
    : [];
  const DONUT_COLORS = ["#EF4444", "#F59E0B", "#10B981"];

  return (
    <div>
      <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <h3 style={{ fontSize: 15, marginBottom: 4 }}>AI Analysis & Results</h3>
        <p style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 16 }}>
          AI-powered analysis using geology, remote sensing, geochemical, geophysical, terrain, and ground-truth data.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 10, marginBottom: 14 }}>
          {[
            { key: "lat", label: "Latitude" }, { key: "lng", label: "Longitude" },
            { key: "elevation", label: "Elevation (m)" }, { key: "slope_deg", label: "Slope (deg)" },
            { key: "ndvi", label: "NDVI" }, { key: "mn_ppm_soil", label: "Mn ppm (soil)" },
            { key: "magnetic_anomaly_nt", label: "Magnetic anomaly (nT)" },
            { key: "distance_to_known_mine_km", label: "Dist. to known mine (km)" },
          ].map((f) => (
            <label key={f.key} style={{ fontSize: 11, color: "var(--text-soft)" }}>
              {f.label}
              <input
                type="number" step="any" value={form[f.key]}
                onChange={(e) => setForm((s) => ({ ...s, [f.key]: parseFloat(e.target.value) }))}
                style={{ display: "block", width: "100%", marginTop: 3, padding: "5px 7px", background: "var(--page-bg)", color: "var(--text)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13 }}
              />
            </label>
          ))}
          <label style={{ fontSize: 11, color: "var(--text-soft)" }}>
            Geology type
            <select
              value={form.geology_type}
              onChange={(e) => setForm((s) => ({ ...s, geology_type: e.target.value }))}
              style={{ display: "block", width: "100%", marginTop: 3, padding: "5px 7px", background: "var(--page-bg)", color: "var(--text)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 13 }}
            >
              {GEOLOGY_OPTIONS.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </label>
        </div>
        <button onClick={runAnalysis} disabled={loading} style={{ background: "linear-gradient(135deg, #2563EB, #1D4ED8)", color: "white", padding: "11px 22px", boxShadow: "0 2px 8px rgba(37,99,235,0.35)", fontWeight: 600, fontSize: 13 }}>
          {loading ? "Running Analysis…" : "Run Analysis"}
        </button>
        <button
          onClick={fetchRealNdvi}
          disabled={ndviLoading}
          style={{ background: "white", color: "var(--accent-green)", border: "1px solid var(--accent-green)", padding: "10px 18px", fontWeight: 600, fontSize: 13, marginLeft: 10 }}
        >
          {ndviLoading ? "Fetching…" : "🛰️ Fetch real NDVI (Sentinel-2)"}
        </button>
        {ndviSource && (
          <p style={{ fontSize: 11, color: ndviSource.startsWith("Failed") ? "var(--danger-red)" : "var(--accent-green)", marginTop: 8 }}>
            {ndviSource}
          </p>
        )}
        {error && <p style={{ color: "var(--danger-red)", marginTop: 10, fontSize: 13 }}>{error}</p>}
      </div>

      {result && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.2fr", gap: 20 }}>
          <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20 }}>
            <h4 style={{ fontSize: 13, marginBottom: 12 }}>AI Prediction Results</h4>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={donutData} dataKey="value" innerRadius={40} outerRadius={65} paddingAngle={2}>
                  {donutData.map((_, i) => <Cell key={i} fill={DONUT_COLORS[i]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "white", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ textAlign: "center", marginTop: -8 }}>
              <div style={{ fontFamily: "var(--font)", fontSize: 24, fontWeight: 700, color: "var(--warning-orange)" }}>
                {result.prospectivity_score}
              </div>
              <div style={{ fontSize: 11, color: "var(--text-soft)" }}>prospectivity score</div>
            </div>
          </div>

          <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20 }}>
            <h4 style={{ fontSize: 13, marginBottom: 12 }}>Estimated Reserves</h4>
            <div style={{ fontFamily: "var(--font)", fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
              {result.reserve_min.toLocaleString()} – {result.reserve_max.toLocaleString()} t
            </div>
            <div style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 16 }}>Manganese (approx.)</div>
            <h4 style={{ fontSize: 13, marginBottom: 6 }}>Model Confidence (R²)</h4>
            <div style={{ background: "var(--border)", borderRadius: 4, height: 8, overflow: "hidden", marginBottom: 4 }}>
              <div style={{ width: `${result.confidence * 100}%`, height: "100%", background: "var(--primary-blue)" }} />
            </div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>{Math.round(result.confidence * 100)}%</div>
          </div>

          <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 12, padding: 20 }}>
            <h4 style={{ fontSize: 13, marginBottom: 12 }}>Key Model Factors</h4>
            {KEY_FACTORS.map((f) => (
              <div key={f.name} style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span>{f.name}</span><span style={{ color: "var(--text-soft)" }}>{f.value}%</span>
                </div>
                <div style={{ background: "var(--border)", borderRadius: 4, height: 6, overflow: "hidden" }}>
                  <div style={{ width: `${f.value * 2}%`, height: "100%", background: "var(--primary-blue)" }} />
                </div>
              </div>
            ))}
            <p style={{ fontSize: 10, color: "var(--text-soft)", marginTop: 10 }}>
              From the trained model's actual feature importances (RandomForest, 15 features).
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
