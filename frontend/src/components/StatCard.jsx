export default function StatCard({ label, value, accent, bg, icon: Icon }) {
  return (
    <div className="card" style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <div style={{
        width: 46, height: 46, borderRadius: 12, background: bg,
        display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
      }}>
        {Icon ? <Icon size={20} color={accent} /> : <span style={{ fontWeight: 700, color: accent }}>{value}</span>}
      </div>
      <div>
        <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text)", lineHeight: 1.1 }}>{value}</div>
        <div style={{ fontSize: 12, color: "var(--text-soft)", fontWeight: 500, marginTop: 2 }}>{label}</div>
      </div>
    </div>
  );
}
