import { useEffect, useState } from "react";
import { LayoutDashboard, Map as MapIcon, Brain, FileBarChart, Lightbulb, Bell, Mountain, Layers, MapPin, TriangleAlert, Gem, UploadCloud, MessageSquare } from "lucide-react";
import { api } from "./api";
import MineMap, { LEVEL_COLORS } from "./components/MineMap";
import ProductionChart from "./components/ProductionChart";
import RiskPanel from "./components/RiskPanel";
import StatCard from "./components/StatCard";
import ProductionShortfallPage from "./components/ProductionShortfallPage";
import AIAnalysisPage from "./components/AIAnalysisPage";
import RecommendationsPage from "./components/RecommendationsPage";
import PointInspector from "./components/PointInspector";
import UploadDataPage from "./components/UploadDataPage";
import ChatPage from "./components/ChatPage";
import PrivacyPolicy from "./components/PrivacyPolicy";
import TermsAndConditions from "./components/TermsAndConditions";
import "./tokens.css";

const NAV = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "Map", icon: MapIcon },
  { label: "Prospectivity Analysis", icon: Brain },
  { label: "Chat", icon: MessageSquare },
  { label: "Reports", icon: FileBarChart },
  { label: "Recommendations", icon: Lightbulb },
  { label: "Upload", icon: UploadCloud },
];

export default function App() {
  const [tab, setTab] = useState("Dashboard");
  const [mines, setMines] = useState([]);
  const [zones, setZones] = useState(null);
  const [moilRealMines, setMoilRealMines] = useState([]);
  const [showMoilReal, setShowMoilReal] = useState(true);
  const [basemap, setBasemap] = useState("gray");
  const [selectedMineId, setSelectedMineId] = useState(null);
  const [production, setProduction] = useState([]);
  const [risk, setRisk] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [loadError, setLoadError] = useState(null);

  // Real v3 pipeline zones (satellite + geology + model + viability), fetched
  // lazily the first time the Map tab is opened — this hits a live grid
  // scoring pass on the backend (cached after the first call per bbox).
  const [liveZones, setLiveZones] = useState(null);
  const [liveZonesError, setLiveZonesError] = useState(null);
  const [waterTable, setWaterTable] = useState(null);
  const [showWaterTable, setShowWaterTable] = useState(false);
  const [clickedLatLng, setClickedLatLng] = useState(null);
  const [pointResult, setPointResult] = useState(null);
  const [pointLoading, setPointLoading] = useState(false);
  const [pointError, setPointError] = useState(null);

  useEffect(() => {
    Promise.all([api.getMines(), api.getProspectivityZones(), api.getMoilRealMines()])
      .then(([m, z, real]) => {
        setMines(m);
        setZones(z);
        setMoilRealMines(real);
        const firstActive = m.find((x) => x.status === "active");
        if (firstActive) setSelectedMineId(firstActive.id);
      })
      .catch(() =>setLoadError( `Could not reach the backend API at ${BASE}. Is it running?`));
  }, []);

  useEffect(() => {
    if (tab !== "Map" || liveZones || liveZonesError) return;
    api.getMapZones()
      .then(setLiveZones)
      .catch((e) => setLiveZonesError(e.message || "Could not load live prospectivity zones."));
  }, [tab, liveZones, liveZonesError]);

  useEffect(() => {
    if (tab !== "Map" || waterTable) return;
    api.getMapWatertable().then(setWaterTable).catch(() => {});
  }, [tab, waterTable]);

  function handleMapClick(lat, lng) {
    setClickedLatLng({ lat, lng });
    setPointResult(null);
    setPointError(null);
    setPointLoading(true);
    api.predictPoint(lat, lng)
      .then(setPointResult)
      .catch((e) => setPointError(e.message || "Point prediction failed."))
      .finally(() => setPointLoading(false));
  }

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
          <div style={{ fontSize: 15, fontWeight: 700 }}>Manganese Intelligence</div>
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
        <div style={{ marginTop: "auto", padding: "12px 8px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ display: "flex", gap: 12, marginBottom: 8 }}>
            <button
              onClick={() => setTab("Privacy")}
              style={{ background: "none", padding: 0, fontSize: 11, color: tab === "Privacy" ? "#93C5FD" : "#64748B" }}
            >
              Privacy
            </button>
            <button
              onClick={() => setTab("Terms")}
              style={{ background: "none", padding: 0, fontSize: 11, color: tab === "Terms" ? "#93C5FD" : "#64748B" }}
            >
              Terms
            </button>
          </div>
          <div style={{ fontSize: 12, color: "#64748B" }}>SIH26009 Prototype</div>
        </div>
      </aside>

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <header style={{
          padding: "16px 32px", borderBottom: "1px solid var(--border)",
          display: "flex", alignItems: "center", gap: 16, background: "var(--card-bg)",
        }}>
          <h1 style={{ fontSize: 18 }}>{tab}</h1>
          <span style={{ color: "var(--text-soft)", fontSize: 13 }}>Satellite, geology and model-based manganese reserve mapping</span>
          <div style={{ marginLeft: "auto" }}>
            <Bell size={18} color="var(--text-soft)" />
          </div>
        </header>

        {tab === "Dashboard" && (
          <main style={{ padding: 28, flex: 1, overflow: "auto" }}>
            <div className="hero-banner" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 24, flexWrap: "wrap" }}>
              <div>
                <h2 style={{ fontSize: 22, marginBottom: 6 }}>Manganese Reserve Intelligence</h2>
                <p style={{ color: "#CBD5E1", fontSize: 14, maxWidth: 480 }}>
                  Using satellite imagery, geological data and a trained prospectivity model to identify manganese reserves and flag production shortfalls. SIH26009.
                </p>
              </div>
              <div style={{ display: "flex", gap: 24, position: "relative", zIndex: 1 }}>
                <div>
                  <div style={{ fontSize: 26, fontWeight: 700, color: "white" }}>{activeMines}</div>
                  <div style={{ fontSize: 11, color: "#93C5FD" }}>Active mines</div>
                </div>
                <div>
                  <div style={{ fontSize: 26, fontWeight: 700, color: "white" }}>{moilRealMines.length}</div>
                  <div style={{ fontSize: 11, color: "#93C5FD" }}>Real MOIL mines</div>
                </div>
                <div>
                  <div style={{ fontSize: 26, fontWeight: 700, color: "white" }}>{highPotential}</div>
                  <div style={{ fontSize: 11, color: "#93C5FD" }}>High potential zones</div>
                </div>
              </div>
            </div>

            <div className="section-label">OVERVIEW</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 28 }}>
              <StatCard label="Mock mines tracked" value={mines.length} accent="var(--primary-blue)" bg="var(--primary-blue-soft)" icon={Layers} />
              <StatCard label="Active mines" value={activeMines} accent="var(--accent-green)" bg="var(--accent-green-soft)" icon={MapPin} />
              <StatCard label="High potential zones" value={highPotential} accent="var(--danger-red)" bg="var(--danger-red-soft)" icon={TriangleAlert} />
              <StatCard label="Real MOIL mines" value={moilRealMines.length} accent="var(--warning-orange)" bg="var(--warning-orange-soft)" icon={Gem} />
            </div>

            <div className="section-label">PRODUCTION AND RISK</div>
            <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 20, marginBottom: 28 }}>
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

            <div className="section-label">MINES AT A GLANCE</div>
            <div className="card">
              {mines.map((m) => (
                <div
                  key={m.id}
                  className={`mine-row ${m.id === selectedMineId ? "active" : ""}`}
                  onClick={() => setSelectedMineId(m.id)}
                >
                  <span style={{
                    width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                    background: m.status === "active" ? "var(--accent-green)" : "var(--warning-orange)",
                  }} />
                  <span style={{ fontSize: 13, fontWeight: 500, flex: 1 }}>{m.name}</span>
                  <span style={{ fontSize: 12, color: "var(--text-soft)" }}>{m.state}</span>
                  <span style={{
                    fontSize: 11, fontWeight: 600, textTransform: "capitalize", padding: "2px 8px", borderRadius: 6,
                    background: m.status === "active" ? "var(--accent-green-soft)" : "var(--warning-orange-soft)",
                    color: m.status === "active" ? "var(--accent-green)" : "var(--warning-orange)",
                  }}>
                    {m.status}
                  </span>
                </div>
              ))}
            </div>
          </main>
        )}

        {tab === "Map" && (
          <main style={{ padding: 28, flex: 1, display: "grid", gridTemplateColumns: "220px minmax(0, 1fr) 300px", gap: 20, maxWidth: "100%", overflow: "hidden" }}>
            <div className="card" style={{ height: "fit-content" }}>
              <h4 style={{ fontSize: 13, marginBottom: 14, color: "var(--text-soft)" }}>MAP LAYERS</h4>
              <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
                {[["gray", "Map"], ["satellite", "Satellite"]].map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setBasemap(key)}
                    style={{
                      flex: 1, padding: "6px 0", fontSize: 12, fontWeight: 600, borderRadius: 6,
                      background: basemap === key ? "var(--primary-blue)" : "var(--page-bg)",
                      color: basemap === key ? "white" : "var(--text-soft)",
                      border: `1px solid ${basemap === key ? "var(--primary-blue)" : "var(--border)"}`,
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, marginBottom: 14, cursor: "pointer" }}>
                <input type="checkbox" checked={showMoilReal} onChange={(e) => setShowMoilReal(e.target.checked)} />
                Real MOIL mines
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, marginBottom: 14, cursor: "pointer" }}>
                <input type="checkbox" checked={showWaterTable} onChange={(e) => setShowWaterTable(e.target.checked)} />
                Water table (known mines)
              </label>
              <div style={{ marginTop: 16, fontSize: 12, color: "var(--text-soft)" }}>
                <div style={{ marginBottom: 8, fontWeight: 600 }}>PROSPECTIVITY</div>
                {["very high", "high", "medium", "low", "very low"].map((level) => (
                  <div key={level} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6, textTransform: "capitalize" }}>
                    <span style={{ width: 10, height: 10, borderRadius: "50%", background: LEVEL_COLORS[level], display: "inline-block" }} />{level}
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, fontSize: 12, color: "var(--text-soft)" }}>
                <div style={{ marginBottom: 8, fontWeight: 600 }}>MARKERS</div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--primary-blue)", display: "inline-block" }} />Mock mine (active)
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 10, height: 10, background: "var(--warning-orange)", display: "inline-block", transform: "rotate(45deg)" }} />Real MOIL mine
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#0EA5E9", display: "inline-block" }} />Water table point
                </div>
              </div>
              {liveZonesError && (
                <p style={{ marginTop: 16, fontSize: 11, color: "var(--danger-red)" }}>{liveZonesError}</p>
              )}
              {!liveZones && !liveZonesError && (
                <p style={{ marginTop: 16, fontSize: 11, color: "var(--text-soft)" }}>Loading live prospectivity grid…</p>
              )}
            </div>
            <div style={{ borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)" }}>
              <MineMap
                mines={mines} zones={liveZones} moilRealMines={moilRealMines}
                showMoilReal={showMoilReal} basemap={basemap}
                selectedMineId={selectedMineId} onSelectMine={setSelectedMineId}
                onMapClick={handleMapClick} clickedLatLng={clickedLatLng}
                waterTable={waterTable} showWaterTable={showWaterTable}
              />
            </div>
            <PointInspector
              latlng={clickedLatLng} loading={pointLoading} error={pointError} result={pointResult}
              onClose={() => setClickedLatLng(null)}
            />
          </main>
        )}

        {tab === "Prospectivity Analysis" && (
          <main style={{ padding: 28, flex: 1 }}>
            <AIAnalysisPage selectedMine={selectedMine} mines={mines} />
          </main>
        )}

        {tab === "Chat" && (
          <main style={{ padding: 28, flex: 1, display: "flex" }}>
            <ChatPage />
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

        {tab === "Upload" && (
          <main style={{ padding: 28, flex: 1 }}>
            <UploadDataPage onMinesReplaced={setMines} />
          </main>
        )}

        {tab === "Privacy" && (
          <main style={{ padding: 28, flex: 1 }}>
            <PrivacyPolicy />
          </main>
        )}

        {tab === "Terms" && (
          <main style={{ padding: 28, flex: 1 }}>
            <TermsAndConditions />
          </main>
        )}
      </div>
    </div>
  );
}
