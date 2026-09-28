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

// multipart/form-data POST for file uploads — no Content-Type header, the
// browser sets the correct boundary itself.
async function postFile(path, file, params = {}) {
  const form = new FormData();
  form.append("file", file);
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`, { method: "POST", body: form });
  if (!res.ok) {
    let detail = `${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
    throw new Error(detail);
  }
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

  // --- Real v3 pipeline (satellite + geology + viability), mounted under /api/map ---
  getMapZones: (bbox, resolution) =>
    get(`/api/map/zones${bbox ? `?bbox=${bbox}${resolution ? `&resolution=${resolution}` : ""}` : ""}`),
  getMapMines: () => get("/api/map/mines"),
  getMapWatertable: () => get("/api/map/watertable"),
  predictPoint: (lat, lng) => get(`/api/map/predict_point?lat=${lat}&lng=${lng}`),

  // --- CSV upload. mode="score": lat/lng rows scored through the v3 pipeline.
  // mode="replace": rows become the live MINES list. See csv_upload.py for the schema. ---
  uploadCsv: (file, { mode = "score", useRealSatellite = false, persist = true } = {}) =>
    postFile("/api/upload/csv", file, {
      mode,
      use_real_satellite: useRealSatellite,
      persist,
    }),
  getUploadTemplateUrl: (mode = "score") => `${BASE}/api/upload/template?mode=${mode}`,

  // --- Tool-calling chatbot ---
  chat: (message, history = []) => post("/api/chat", { message, history }),
};
