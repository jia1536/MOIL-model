import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Cell, Tooltip, Legend, CartesianGrid, ResponsiveContainer } from "recharts";
import { api } from "../api";

const STATUS_STYLE = {
  Critical: { color: "var(--danger-red)", bg: "var(--danger-red-soft)" },
  Watch: { color: "var(--warning-orange)", bg: "var(--warning-orange-soft)" },
  Adequate: { color: "var(--accent-green)", bg: "var(--accent-green-soft)" },
  "Not producing": { color: "var(--text-soft)", bg: "var(--page-bg)" },
};

const fmt = (n) => (n === null || n === undefined ? "-" : Number(n).toLocaleString("en-IN"));
const pct = (n) => (n === null || n === undefined ? "-" : `${n}%`);
const signedPct = (n) => (n === null || n === undefined ? "-" : `${n > 0 ? "+" : ""}${n}%`);

const th = { padding: "8px 6px", borderBottom: "1px solid var(--border)", fontWeight: 600 };
const td = { padding: "8px 6px", borderBottom: "1px solid var(--border)" };
const tooltipStyle = { background: "white", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 };

function Notes({ items }) {
  if (!items?.length) return null;
  return (
    <ul style={{ margin: "12px 0 0", paddingLeft: 18, fontSize: 11, color: "var(--text-soft)", lineHeight: 1.6 }}>
      {items.map((n) => <li key={n}>{n}</li>)}
    </ul>
  );
}

function CountrySection({ data }) {
  const india = data.india;
  const chartData = data.countries.filter((c) => c.reserves_kt);
  return (
    <div className="card" style={{ marginBottom: 28 }}>
      <h3 style={{ fontSize: 15, marginBottom: 4 }}>India against other producing countries</h3>
      {india && (
        <p style={{ fontSize: 13, color: "var(--text-soft)", marginBottom: 16 }}>
          India ranks {india.rank_by_reserves} of {data.countries_ranked.by_reserves} listed countries by reserves and{" "}
          {india.rank_by_production} of {data.countries_ranked.by_production} by 2020 production. At the 2020 rate,
          reserves last about {india.years_at_2020_rate} years.
        </p>
      )}

      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Reserves (thousand tonnes, metal content)</div>
      <ResponsiveContainer width="100%" height={chartData.length * 34 + 30}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: "var(--text-soft)" }} tickFormatter={(v) => fmt(v)} />
          <YAxis type="category" dataKey="country" width={90} tick={{ fontSize: 12, fill: "var(--text)" }} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmt(v)} />
          <Bar dataKey="reserves_kt" name="Reserves" radius={[0, 4, 4, 0]}>
            {chartData.map((c) => (
              <Cell key={c.country} fill={c.country === "India" ? "var(--primary-blue)" : "#94A3B8"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div style={{ overflowX: "auto", marginTop: 16 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--text-soft)", fontSize: 12 }}>
              <th style={th}>Country</th>
              <th style={th}>Reserves (kt)</th>
              <th style={th}>Production 2020 (kt)</th>
              <th style={th}>Share of world reserves</th>
              <th style={th}>Share of world production</th>
              <th style={th}>Years at 2020 rate</th>
              <th style={th}>Production change 2018 to 2020</th>
            </tr>
          </thead>
          <tbody>
            {data.countries.map((c) => (
              <tr key={c.country} style={{ background: c.country === "India" ? "var(--primary-blue-soft)" : "transparent", fontWeight: c.country === "India" ? 600 : 400 }}>
                <td style={td}>{c.country}</td>
                <td style={td}>{fmt(c.reserves_kt)}</td>
                <td style={td}>{fmt(c.production_2020_kt)}</td>
                <td style={td}>{pct(c.share_of_world_reserves_pct)}</td>
                <td style={td}>{pct(c.share_of_world_production_pct)}</td>
                <td style={td}>{c.years_at_2020_rate ?? "-"}</td>
                <td style={{ ...td, color: c.production_change_pct < 0 ? "var(--danger-red)" : "var(--accent-green)" }}>
                  {signedPct(c.production_change_pct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Notes items={data.notes} />
    </div>
  );
}

function StateSection({ data }) {
  const chartData = data.states.map((s) => ({
    state: s.state,
    "Proven reserves": s.reserves_kt,
    "Remaining resources": s.remaining_resources_kt,
  }));
  return (
    <div className="card" style={{ marginBottom: 28 }}>
      <h3 style={{ fontSize: 15, marginBottom: 4 }}>State comparison</h3>
      <p style={{ fontSize: 13, color: "var(--text-soft)", marginBottom: 16 }}>
        Proven reserves and remaining resources by state, with 2020-21 production. Manganese ore, thousand tonnes.
      </p>

      <ResponsiveContainer width="100%" height={data.states.length * 32 + 50}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: "var(--text-soft)" }} tickFormatter={(v) => fmt(v)} />
          <YAxis type="category" dataKey="state" width={110} tick={{ fontSize: 12, fill: "var(--text)" }} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmt(v)} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Proven reserves" stackId="a" fill="var(--primary-blue)" />
          <Bar dataKey="Remaining resources" stackId="a" fill="#BFDBFE" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <div style={{ overflowX: "auto", marginTop: 16 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--text-soft)", fontSize: 12 }}>
              <th style={th}>State</th>
              <th style={th}>Reserves (kt)</th>
              <th style={th}>Remaining resources (kt)</th>
              <th style={th}>Share of national resources</th>
              <th style={th}>Production 2020-21 (t)</th>
              <th style={th}>Share of national production</th>
              <th style={th}>Change since 2018-19</th>
            </tr>
          </thead>
          <tbody>
            {data.states.map((s) => (
              <tr key={s.state}>
                <td style={{ ...td, fontWeight: 500 }}>{s.state}</td>
                <td style={td}>{fmt(s.reserves_kt)}</td>
                <td style={td}>{fmt(s.remaining_resources_kt)}</td>
                <td style={td}>{pct(s.share_of_national_resources_pct)}</td>
                <td style={td}>{fmt(s.production_2020_21_t)}</td>
                <td style={td}>{pct(s.share_of_national_production_pct)}</td>
                <td style={{ ...td, color: s.production_change_pct < 0 ? "var(--danger-red)" : "var(--accent-green)" }}>
                  {signedPct(s.production_change_pct)}
                </td>
              </tr>
            ))}
            <tr style={{ fontWeight: 700, background: "var(--page-bg)" }}>
              <td style={td}>{data.national.state}</td>
              <td style={td}>{fmt(data.national.reserves_kt)}</td>
              <td style={td}>{fmt(data.national.remaining_resources_kt)}</td>
              <td style={td}>100%</td>
              <td style={td}>{fmt(data.national.production_2020_21_t)}</td>
              <td style={td}>100%</td>
              <td style={{ ...td, color: data.national.production_change_pct < 0 ? "var(--danger-red)" : "var(--accent-green)" }}>
                {signedPct(data.national.production_change_pct)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <Notes items={data.notes} />
    </div>
  );
}

function DepletionSection({ data }) {
  const producing = data.states.filter((s) => s.years_of_reserves !== null);
  const idle = data.states.filter((s) => s.years_of_reserves === null);
  const scaleMax = 100;
  const nat = data.national;

  return (
    <div className="card">
      <h3 style={{ fontSize: 15, marginBottom: 4 }}>Reserve depletion</h3>
      <p style={{ fontSize: 13, color: "var(--text-soft)", marginBottom: 16 }}>
        Years of proven reserves left at each state's 2020-21 production rate, shortest first. Critical is under{" "}
        {data.thresholds.critical_below_years} years and Watch is under {data.thresholds.watch_below_years} years.
      </p>

      {nat && (
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, padding: "12px 14px", borderRadius: 8, background: "var(--page-bg)", marginBottom: 18 }}>
          <span style={{ fontSize: 26, fontWeight: 700 }}>{nat.years_of_reserves}</span>
          <span style={{ fontSize: 13, color: "var(--text-soft)" }}>
            years of proven reserves nationally at the 2020-21 rate ({fmt(nat.production_2020_21_t)} t a year), or{" "}
            {nat.years_of_total_resources} years counting remaining resources.
          </span>
        </div>
      )}

      {producing.map((s) => {
        const style = STATUS_STYLE[s.status];
        return (
          <div key={s.state} style={{ display: "grid", gridTemplateColumns: "130px 1fr 150px 90px", alignItems: "center", gap: 14, padding: "9px 0", borderBottom: "1px solid var(--border)" }}>
            <span style={{ fontSize: 13, fontWeight: 500 }}>{s.state}</span>
            <div style={{ background: "var(--border)", borderRadius: 4, height: 8, overflow: "hidden" }}>
              <div style={{ width: `${Math.min(s.years_of_reserves, scaleMax)}%`, height: "100%", background: style.color }} />
            </div>
            <span style={{ fontSize: 12, color: "var(--text-soft)" }}>
              <strong style={{ color: "var(--text)", fontSize: 14 }}>{s.years_of_reserves}</strong> years
              {" "}({s.years_of_total_resources} incl. resources)
            </span>
            <span style={{ fontSize: 11, fontWeight: 600, textAlign: "center", padding: "3px 0", borderRadius: 6, background: style.bg, color: style.color }}>
              {s.status}
            </span>
          </div>
        );
      })}

      {idle.length > 0 && (
        <p style={{ fontSize: 12, color: "var(--text-soft)", marginTop: 14 }}>
          No production recorded in 2020-21: {idle.map((s) => s.state).join(", ")}.
        </p>
      )}
      <p style={{ fontSize: 11, color: "var(--text-soft)", marginTop: 10 }}>{data.thresholds.basis}</p>
      <p style={{ fontSize: 11, color: "var(--text-soft)", marginTop: 4 }}>Bars are scaled to {scaleMax} years.</p>
    </div>
  );
}

export default function ComparePage() {
  const [countries, setCountries] = useState(null);
  const [states, setStates] = useState(null);
  const [depletion, setDepletion] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getCompareCountries(), api.getCompareStates(), api.getDepletion()])
      .then(([c, s, d]) => { setCountries(c); setStates(s); setDepletion(d); })
      .catch((e) => setError(e.message || "Could not load comparison data."));
  }, []);

  if (error) return <div className="card" style={{ color: "var(--danger-red)", fontSize: 13 }}>{error}</div>;
  if (!countries || !states || !depletion) {
    return <p style={{ color: "var(--text-soft)", fontSize: 13 }}>Loading comparison data...</p>;
  }

  return (
    <div style={{ maxWidth: 1100 }}>
      <CountrySection data={countries} />
      <StateSection data={states} />
      <DepletionSection data={depletion} />
    </div>
  );
}
