import { useState } from "react";
import { api } from "../api";

const GEOLOGY_OPTIONS = ["gondite_archean", "archean", "kodurite_archean", "laterite"];

const DEFAULTS = {
  lat: 21.8, lng: 80.18, elevation: 400, slope_deg: 12,
  drainage_density: 1.5, ndvi: 0.6, ndwi: 0.1, land_surface_temp: 30,
  mineral_alteration_index: 0.7, mn_ppm_soil: 1600, magnetic_anomaly_nt: 95,
  distance_to_fault_km: 3, distance_to_known_mine_km: 2,
  geology_type: "gondite_archean",
};

const NUMERIC_FIELDS = [
  { key: "lat", label: "Latitude" },
  { key: "lng", label: "Longitude" },
  { key: "elevation", label: "Elevation (m)" },
  { key: "slope_deg", label: "Slope (deg)" },
  { key: "drainage_density", label: "Drainage density" },
  { key: "ndvi", label: "NDVI (0-1)" },
  { key: "ndwi", label: "NDWI (-1 to 1)" },
  { key: "land_surface_temp", label: "Land surface temp (C)" },
  { key: "mineral_alteration_index", label: "Mineral alteration index" },
  { key: "mn_ppm_soil", label: "Mn ppm (soil)" },
  { key: "magnetic_anomaly_nt", label: "Magnetic anomaly (nT)" },
  { key: "distance_to_fault_km", label: "Distance to fault (km)" },
  { key: "distance_to_known_mine_km", label: "Distance to known mine (km)" },
];

export default function ProspectivityTool() {
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
      const numericForm = { ...form };
      NUMERIC_FIELDS.forEach((f) => { numericForm[f.key] = parseFloat(form[f.key]); });
      const res = await api.predictProspectivity(numericForm);
      setResult(res);
    } catch (e) {
      setError("Could not reach the prediction API. Is the backend running on port 8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p style={{ color: "var(--text-soft)", fontSize: 14, marginBottom: 16 }}>
        Enter site conditions to get a live prospectivity score from the trained model.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12, marginBottom: 16 }}>
        {NUMERIC_FIELDS.map((f) => (
          <label key={f.key} style={{ fontSize: 12, color: "var(--text-soft)" }}>
            {f.label}
            <input
              type="number"
              step="any"
              value={form[f.key]}
              onChange={(e) => update(f.key, e.target.value)}
              style={{
                display: "block", width: "100%", marginTop: 4, padding: "6px 8px",
                border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font)", fontSize: 14, background: "var(--page-bg)", color: "var(--text)",
              }}
            />
          </label>
        ))}
        <label style={{ fontSize: 12, color: "var(--text-soft)" }}>
          Geology type
          <select
            value={form.geology_type}
            onChange={(e) => update("geology_type", e.target.value)}
            style={{
              display: "block", width: "100%", marginTop: 4, padding: "6px 8px",
              border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font)", fontSize: 14, background: "var(--page-bg)", color: "var(--text)",
            }}
          >
            {GEOLOGY_OPTIONS.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </label>
      </div>

      <button
        onClick={runPrediction}
        disabled={loading}
        style={{
          background: "linear-gradient(135deg, #2563EB, #1D4ED8)", color: "white", padding: "11px 22px", boxShadow: "0 2px 8px rgba(37,99,235,0.35)",
          fontSize: 14, fontWeight: 600, borderRadius: 8,
        }}
      >
        {loading ? "Predicting..." : "Run prediction"}
      </button>

      {error && <p style={{ color: "var(--danger-red)", marginTop: 12 }}>{error}</p>}

      {result && (
        <div style={{
          marginTop: 20, background: "white", border: "1px solid var(--border)",
          borderRadius: 10, padding: 20, display: "flex", gap: 32, flexWrap: "wrap",
        }}>
          <div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>Prospectivity score</div>
            <div style={{ fontFamily: "var(--font)", fontSize: 32, fontWeight: 700, color: "var(--warning-orange)" }}>
              {result.prospectivity_score}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>Model confidence (R²)</div>
            <div style={{ fontFamily: "var(--font)", fontSize: 32, fontWeight: 700 }}>
              {result.confidence}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--text-soft)" }}>Estimated reserve range</div>
            <div style={{ fontFamily: "var(--font)", fontSize: 20, fontWeight: 600 }}>
              {result.reserve_min.toLocaleString()} – {result.reserve_max.toLocaleString()} t
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
