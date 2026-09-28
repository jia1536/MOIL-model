const LEVEL_COLOR = {
  "very high": "var(--danger-red)",
  high: "var(--warning-orange)",
  medium: "var(--warning-orange)",
  low: "var(--accent-green)",
  "very low": "var(--accent-green)",
};

function GradeBreakdown({ grade }) {
  if (!grade) return null;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 11, color: "var(--text-soft)" }}>
        Ore grade (district breakdown, {grade.district}, {grade.state})
      </div>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
        {grade.high_grade_share_pct}% high grade ({">"}35% Mn)
      </div>
      <div style={{ fontSize: 11, color: "var(--text-soft)" }}>
        {grade.total_quantity_tonnes.toLocaleString()} t total across {grade.num_mines} mine{grade.num_mines === 1 ? "" : "s"} in the district
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  if (value === undefined || value === null) return null;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 11, color: "var(--text-soft)" }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

export default function PointInspector({ loading, error, result, latlng, onClose }) {
  if (!latlng) {
    return (
      <div className="card" style={{ height: "fit-content" }}>
        <h4 style={{ fontSize: 13, marginBottom: 10, color: "var(--text-soft)" }}>POINT INSPECTOR</h4>
        <p style={{ fontSize: 12, color: "var(--text-soft)" }}>
          Click anywhere on the map to run the live pipeline (satellite → geology → model → viability) for that exact point.
        </p>
      </div>
    );
  }

  return (
    <div className="card" style={{ height: "fit-content" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <h4 style={{ fontSize: 13, color: "var(--text-soft)" }}>POINT INSPECTOR</h4>
        <button onClick={onClose} style={{ background: "none", fontSize: 12, color: "var(--text-soft)", padding: 0 }}>✕</button>
      </div>
      <div style={{ fontSize: 11, color: "var(--text-soft)", marginBottom: 12 }}>
        {latlng.lat.toFixed(4)}, {latlng.lng.toFixed(4)}
      </div>

      {loading && <p style={{ fontSize: 13, color: "var(--text-soft)" }}>Running live pipeline…</p>}
      {error && <p style={{ fontSize: 13, color: "var(--danger-red)" }}>{error}</p>}

      {result && (
        <>
          <div style={{
            display: "inline-block", padding: "3px 10px", borderRadius: 20, marginBottom: 14,
            background: LEVEL_COLOR[result.level] || "var(--border)", color: "white", fontSize: 12, fontWeight: 600,
          }}>
            {result.level} · {result.prospectivity.prospectivity_score.toFixed(3)}
          </div>

          <Stat label="Nearest known mine" value={result.nearest_mine} />
          <Stat label="Confidence for this point" value={`${Math.round(result.prospectivity.confidence * 100)}% tree agreement`} />
          <Stat label="Overall model skill (R²)" value={result.prospectivity.model_r2} />
          <Stat
            label="Estimated reserve range"
            value={`${result.prospectivity.reserve_min_tonnes?.toLocaleString?.() ?? "-"} – ${result.prospectivity.reserve_max_tonnes?.toLocaleString?.() ?? "-"} t`}
          />
          <Stat label="Viability index" value={result.viability?.viability_index} />
          {result.forecast && <Stat label="Production shortfall risk" value={result.forecast.risk_level} />}
          <Stat
            label="Thickness (illustrative)"
            value={result.thickness ? `${result.thickness.thickness_m} m` : undefined}
          />
          <Stat
            label="Water table depth (illustrative)"
            value={result.water_table ? `${result.water_table.water_table_depth_m} m` : undefined}
          />
          <GradeBreakdown grade={result.grade} />
          {result.companies?.length > 0 && (
            <Stat label="Known operators nearby" value={result.companies.join(", ")} />
          )}

          {result.top_features?.length > 0 && (
            <div style={{ marginTop: 6 }}>
              <div style={{ fontSize: 11, color: "var(--text-soft)", marginBottom: 6 }}>TOP CONTRIBUTING FEATURES</div>
              {result.top_features.map((f) => (
                <div key={f.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                  <span>{f.name}</span>
                  <span style={{ fontWeight: 600, color: f.contribution >= 0 ? "var(--accent-green)" : "var(--danger-red)" }}>
                    {f.contribution >= 0 ? "+" : ""}{f.contribution}
                  </span>
                </div>
              ))}
            </div>
          )}

          <p style={{ fontSize: 10, color: "var(--text-soft)", marginTop: 14 }}>
            Thickness, water table and per-point grade are illustrative estimates calibrated to real
            state/geology averages, not borehole or CGWB measurements.
          </p>
        </>
      )}
    </div>
  );
}
