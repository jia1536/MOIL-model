import { useEffect, useState } from "react";
import { Lightbulb } from "lucide-react";
import { api } from "../api";

const LEVEL_BADGE = {
  High: { bg: "var(--danger-red-soft)", color: "var(--danger-red)" },
  Medium: { bg: "var(--warning-orange-soft)", color: "var(--warning-orange)" },
  Low: { bg: "var(--accent-green-soft)", color: "var(--accent-green)" },
};

export default function RecommendationsPage({ mines }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const activeMines = mines.filter((m) => m.status === "active");
    Promise.all(activeMines.map((m) => api.getRecommendations(m.id)))
      .then((results) => {
        const rows = activeMines.map((m, i) => {
          const rec = results[i][0];
          return rec ? { mine: m.name, ...rec } : null;
        }).filter(Boolean);
        setItems(rows);
        setLoading(false);
      });
  }, [mines]);

  return (
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: "var(--warning-orange-soft)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Lightbulb size={18} color="var(--warning-orange)" />
        </div>
        <h3 style={{ fontSize: 16 }}>Recommendations</h3>
      </div>
      <p style={{ color: "var(--text-soft)", fontSize: 13, marginBottom: 20 }}>
        AI-driven recommendations for exploration and production improvement, based on each mine's top risk factor.
      </p>

      {loading ? (
        <p style={{ color: "var(--text-soft)" }}>Loading…</p>
      ) : (
        items.map((item, i) => {
          const badge = LEVEL_BADGE[item.risk_level] || LEVEL_BADGE.Medium;
          return (
            <div key={item.mine} style={{
              display: "flex", alignItems: "center", gap: 16, padding: "16px 0",
              borderTop: i > 0 ? "1px solid var(--border)" : "none",
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%", background: "var(--primary-blue-soft)",
                color: "var(--primary-blue)", display: "flex", alignItems: "center", justifyContent: "center",
                fontWeight: 700, fontSize: 13, flexShrink: 0,
              }}>
                {i + 1}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{item.mine}</div>
                <div style={{ fontSize: 13, color: "var(--text-soft)" }}>
                  <strong>{item.primary_cause}:</strong> {item.recommendation}
                </div>
              </div>
              <span style={{
                background: badge.bg, color: badge.color, fontSize: 12, fontWeight: 600,
                padding: "4px 10px", borderRadius: 6, flexShrink: 0,
              }}>
                {item.risk_level}
              </span>
            </div>
          );
        })
      )}
    </div>
  );
}
