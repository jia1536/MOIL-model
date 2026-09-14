import { useEffect, useState } from "react";
import { LayoutDashboard, Map as MapIcon, Brain, FileBarChart, Lightbulb, Settings, Bell, Mountain, Layers, MapPin, TriangleAlert, Gem, UploadCloud } from "lucide-react";
import { api } from "./api";
import MineMap from "./components/MineMap";
import ProductionChart from "./components/ProductionChart";
import RiskPanel from "./components/RiskPanel";
import ProspectivityTool from "./components/ProspectivityTool";
import StatCard from "./components/StatCard";
import ProductionShortfallPage from "./components/ProductionShortfallPage";
import AIAnalysisPage from "./components/AIAnalysisPage";
import RecommendationsPage from "./components/RecommendationsPage";
import UploadDataPage from "./components/UploadDataPage";
import "./tokens.css";

const NAV = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "Map", icon: MapIcon },
  { label: "Reports", icon: FileBarChart },
  { label: "Recommendations", icon: Lightbulb },
  { label: "Upload Data", icon: UploadCloud },
  { label: "AI Analysis", icon: Settings },
];

export default function App() {
  const [tab, setTab] = useState("Dashboard");
  const [mines, setMines] = useState([]);
  const [zones, setZones] = useState(null);
  const [moilRealMines, setMoilRealMines] = useState([]);
  const [showMoilReal, setShowMoilReal] = useState(true);
  const [selectedMineId, setSelectedMineId] = useState(null);
  const [production, setProduction] = useState([]);
  const [risk, setRisk] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    Promise.all([api.getMines(), api.getProspectivityZones(), api.getMoilRealMines()])
      .then(([m, z, real]) => {
        setMines(m);
        setZones(z);
        setMoilRealMines(real);
        const firstActive = m.find((x) => x.status === "active");
        if (firstActive) setSelectedMineId(firstActive.id);
      })
      .catch(() => setLoadError("Could not reach the backend API at http://127.0.0.1:8000. Is it running?"));
  }, []);

  useEffect(() => {
    if (!selectedMineId) return;
    api.getProduction(selectedMineId).then(setProduction).catch(() => setProduction([]));
    api.getRisks(selectedMineId).then((r) => setRisk(r[0] || null)).catch(() => setRisk(null));
    api.getRecommendations(selectedMineId).then((r) => setRecommendation(r[0] || null)).catch(() => setRecommendation(null));
    api.getForecast(selectedMineId).then(setForecast).catch(() => setForecast([]));
  }, [selectedMineId]);

  const selectedMine = mines.find((m) => m.id === selectedMineId);
  const activeMines = mines.filter((m) => m.status === "active").length;
  const highPotential = zones ? zones.features.filter((f) => f.properties.prospectivity_score > 0.6).length : 0;

  if (loadError) {
    return (
      <div style={{ padding: 40, fontFamily: "var(--font)" }}>
        <h2>Can't reach the backend</h2>
        <p style={{ color: "var(--text-soft)" }}>{loadError}</p>
        <p style={{ color: "var(--text-soft)", fontSize: 14 }}>
          Start it with: <code>cd backend && uvicorn main:app --reload --port 8000</code>
        </p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "var(--page-bg)" }}>
      {/* Sidebar */}
      <aside style={{
        width: 220, background: "var(--dark-bg)", color: "var(--light-text)",
        padding: "20px 14px", display: "flex", flexDirection: "column", gap: 2,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "4px 8px 24px" }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "var(--primary-blue)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Mountain size={18} color="white" />
          </div>
          <div style={{ fontSize: 15, fontWeight: 700 }}>Manganese AI</div>
        </div>
        {NAV.map(({ label, icon: Icon }) => (
          <button
            key={label}
            onClick={() => setTab(label)}
            className={`nav-btn ${tab === label ? "active" : ""}`}
            style={{
              display: "flex", alignItems: "center", gap: 10, textAlign: "left",
              padding: "10px 12px", fontSize: 14, fontWeight: 500,
              background: tab === label ? "rgba(37,99,235,0.18)" : "transparent",
              color: tab === label ? "#93C5FD" : "#94A3B8",
            }}
          >
            <Icon size={17} />
            {label}
          </button>
        ))}
        <div style={{ marginTop: "auto", padding: "12px 8px", borderTop: "1px solid rgba(255,255,255,0.08)", fontSize: 12, color: "#64748B" }}>
          SIH26009 Prototype
        </div>
      </aside>

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <header style={{
          padding: "16px 32px", borderBottom: "1px solid var(--border)",
          display: "flex", alignItems: "center", gap: 16, background: "var(--card-bg)",
        }}>
          <h1 style={{ fontSize: 18 }}>{tab}</h1>
          <span style={{ color: "var(--text-soft)", fontSize: 13 }}>AI + Space Technology for Manganese Reserves</span>
          <div style={{ marginLeft: "auto" }}>
            <Bell size={18} color="var(--text-soft)" />
          </div>
        </header>

        {tab === "Dashboard" && (
          <main style={{ padding: 28, flex: 1, overflow: "auto" }}>
            <div className="hero-banner" style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 22, marginBottom: 6 }}>Manganese Reserve Intelligence</h2>
              <p style={{ color: "#CBD5E1", fontSize: 14, maxWidth: 520 }}>
                A prototype dashboard for monitoring manganese mines and prospectivity zones, with AI-driven risk analysis and recommendations. 
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
              <StatCard label="Mock mines tracked" value={mines.length} accent="var(--primary-blue)" bg="var(--primary-blue-soft)" icon={Layers} />
              <StatCard label="Active mines" value={activeMines} accent="var(--accent-green)" bg="var(--accent-green-soft)" icon={MapPin} />
              <StatCard label="High potential zones" value={highPotential} accent="var(--danger-red)" bg="var(--danger-red-soft)" icon={TriangleAlert} />
              <StatCard label="Real MOIL mines" value={moilRealMines.length} accent="var(--warning-orange)" bg="var(--warning-orange-soft)" icon={Gem} />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 20 }}>
              <div className="card">
                <h3 style={{ fontSize: 15, marginBottom: 16 }}>Production: planned vs. actual</h3>
                <ProductionChart data={production} />
              </div>
              <div className="card">
                <h3 style={{ fontSize: 15, marginBottom: 4 }}>{selectedMine ? selectedMine.name : "Select a mine"}</h3>
                {selectedMine && <p style={{ color: "var(--text-soft)", fontSize: 13, marginBottom: 16 }}>{selectedMine.state} · {selectedMine.status}</p>}
                <RiskPanel risk={risk} recommendation={recommendation} forecast={forecast} />
              </div>
            </div>
          </main>
        )}

        {tab === "Map" && (
          <main style={{ padding: 28, flex: 1, display: "grid", gridTemplateColumns: "220px 1fr", gap: 20 }}>
            <div className="card" style={{ height: "fit-content" }}>
              <h4 style={{ fontSize: 13, marginBottom: 14, color: "var(--text-soft)" }}>MAP LAYERS</h4>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, marginBottom: 14, cursor: "pointer" }}>
                <input type="checkbox" checked={showMoilReal} onChange={(e) => setShowMoilReal(e.target.checked)} />
                Real MOIL mines
              </label>
              <div style={{ marginTop: 16, fontSize: 12, color: "var(--text-soft)" }}>
                <div style={{ marginBottom: 8, fontWeight: 600 }}>PROSPECTIVITY</div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--danger-red)", display: "inline-block" }} />High
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--warning-orange)", display: "inline-block" }} />Medium
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--accent-green)", display: "inline-block" }} />Low
                </div>
              </div>
              <div style={{ marginTop: 16, fontSize: 12, color: "var(--text-soft)" }}>
                <div style={{ marginBottom: 8, fontWeight: 600 }}>MARKERS</div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--primary-blue)", display: "inline-block" }} />Mock mine (active)
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 10, height: 10, background: "var(--warning-orange)", display: "inline-block", transform: "rotate(45deg)" }} />Real MOIL mine
                </div>
              </div>
            </div>
            <div style={{ borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)" }}>
              <MineMap
                mines={mines} zones={zones} moilRealMines={moilRealMines}
                showMoilReal={showMoilReal}
                selectedMineId={selectedMineId} onSelectMine={setSelectedMineId}
              />
            </div>
          </main>
        )}

        {tab === "AI Analysis" && (
          <main style={{ padding: 28, flex: 1 }}>
            <AIAnalysisPage selectedMine={selectedMine} />
          </main>
        )}

        {tab === "Reports" && (
          <main style={{ padding: 28, flex: 1 }}>
            <ProductionShortfallPage mines={mines} zones={zones} />
          </main>
        )}

        {tab === "Recommendations" && (
          <main style={{ padding: 28, flex: 1 }}>
            <RecommendationsPage mines={mines} />
          </main>
        )}

        {tab === "Upload Data" && (
          <main style={{ padding: 28, flex: 1 }}>
            <UploadDataPage />
          </main>
        )}

        {tab === "Settings" && (
          <main style={{ padding: 28, flex: 1 }}>
            <div className="card">
              <h3 style={{ fontSize: 15, marginBottom: 12 }}>Prospectivity model explorer</h3>
              <ProspectivityTool />
            </div>
          </main>
        )}
      </div>
    </div>
  );
}
