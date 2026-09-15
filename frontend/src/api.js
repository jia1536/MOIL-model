const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  getMines: () => get("/api/mines"),
  getProduction: (mineId) => get(`/api/production${mineId ? `?mine_id=${mineId}` : ""}`),
  getEquipment: (mineId) => get(`/api/equipment${mineId ? `?mine_id=${mineId}` : ""}`),
  getDowntime: (mineId) => get(`/api/equipment_downtime${mineId ? `?mine_id=${mineId}` : ""}`),
  getForecast: (mineId) => get(`/api/forecast${mineId ? `?mine_id=${mineId}` : ""}`),
  getRisks: (mineId) => get(`/api/risks${mineId ? `?mine_id=${mineId}` : ""}`),
  getRecommendations: (mineId) => get(`/api/recommendations${mineId ? `?mine_id=${mineId}` : ""}`),
  getProspectivityZones: () => get("/api/prospectivity_zones"),
  getMoilRealMines: () => get("/api/moil_real_mines"),
  predictProspectivity: (features) => post("/api/predict/prospectivity", features),
  predictForecast: (features) => post("/api/predict/forecast", features),
  getRealNdvi: (lat, lng) => get(`/api/satellite/ndvi?lat=${lat}&lng=${lng}`),
};
