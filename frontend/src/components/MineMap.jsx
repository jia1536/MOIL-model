import { MapContainer, TileLayer, CircleMarker, Marker, Popup, GeoJSON, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const STATUS_COLOR = { active: "#2563EB", prospective: "#F59E0B" };

// Matches routes_map.py's LEVEL_BREAKS exactly (5-way natural-breaks
// classification of the prospectivity score), not an approximation.
export const LEVEL_COLORS = {
  "very low": "#94A3B8",
  low: "#10B981",
  medium: "#F59E0B",
  high: "#F97316",
  "very high": "#EF4444",
};

// Real v3 zones (/api/map/zones) use "score"/"level"; the legacy mock
// GeoJSON (/api/prospectivity_zones) used "prospectivity_score" only — fall
// back to a 3-way score split if "level" isn't present.
function zoneStyle(feature) {
  const { level, score, prospectivity_score } = feature.properties;
  const s = score ?? prospectivity_score;
  const color = level
    ? LEVEL_COLORS[level] || "#94A3B8"
    : s > 0.6 ? "#EF4444" : s > 0.4 ? "#F59E0B" : "#10B981";
  return { color, weight: 1, fillColor: color, fillOpacity: 0.35 };
}

function featureRow(f) {
  const positive = f.contribution >= 0;
  return `<div style="display:flex;justify-content:space-between;font-size:11px;padding:2px 0;">
    <span>${f.name}</span>
    <span style="font-weight:600;color:${positive ? "#059669" : "#DC2626"}">${positive ? "+" : ""}${f.contribution}</span>
  </div>`;
}

function bindZonePopup(feature, layer) {
  const p = feature.properties;
  const score = p.score ?? p.prospectivity_score;
  if (score === undefined) return;

  const featureRows = (p.top_features || []).slice(0, 4).map(featureRow).join("");
  const vc = p.viability_components;
  const componentsHtml = vc
    ? `<div style="margin-top:6px;padding-top:6px;border-top:1px solid #eee;font-size:11px;">
        <div style="color:#888;margin-bottom:2px;">Viability breakdown</div>
        <div>Prospectivity: ${vc.prospectivity_score}</div>
        <div>Shortfall risk: ${vc.shortfall_risk_score}</div>
        <div>Water stress: ${vc.water_stress_score}</div>
        <div>Reserve urgency: ${vc.reserve_urgency_score}</div>
      </div>`
    : "";

  layer.bindPopup(
    `<div style="font-size:12px;line-height:1.5;min-width:190px">
      <strong>Score: ${score.toFixed(3)}</strong> (${p.level || "-"})<br/>
      ${p.viability_index !== undefined ? `Viability index: ${p.viability_index}<br/>` : ""}
      ${featureRows ? `<div style="margin-top:4px;color:#888;font-size:11px;">Key drivers</div>${featureRows}` : ""}
      ${componentsHtml}
      <span style="color:#8FA3B8;font-size:11px;display:block;margin-top:6px;">Click elsewhere on the map for a full point report.</span>
    </div>`
  );
}

const moilIcon = L.divIcon({
  className: "",
  html: `<div style="width:14px;height:14px;background:#F59E0B;border:2px solid #F8FAFC;border-radius:3px;transform:rotate(45deg);box-shadow:0 0 0 2px #F59E0B55;"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

const clickIcon = L.divIcon({
  className: "",
  html: `<div style="width:16px;height:16px;border-radius:50%;background:#2563EB;border:3px solid white;box-shadow:0 0 0 3px #2563EB55;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

// Must live inside <MapContainer> — useMapEvents attaches to the map instance
// created by the nearest MapContainer ancestor.
function ClickCatcher({ onMapClick }) {
  useMapEvents({
    click(e) {
      if (onMapClick) onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

const BASEMAPS = {
  gray: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    attribution: "Tiles &copy; Esri, HERE, Garmin, FAO, NOAA, USGS",
  },
  satellite: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community",
  },
};

export default function MineMap({
  mines, zones, moilRealMines, selectedMineId, onSelectMine, showMoilReal,
  onMapClick, clickedLatLng, waterTable, showWaterTable, basemap = "gray",
}) {
  const tile = BASEMAPS[basemap] || BASEMAPS.gray;
  return (
    <MapContainer
      center={[20.5, 80.5]}
      zoom={5}
      scrollWheelZoom={true}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer attribution={tile.attribution} url={tile.url} />
      {onMapClick && <ClickCatcher onMapClick={onMapClick} />}

      {zones && <GeoJSON data={zones} style={zoneStyle} onEachFeature={bindZonePopup} />}

      {clickedLatLng && (
        <Marker position={[clickedLatLng.lat, clickedLatLng.lng]} icon={clickIcon} />
      )}

      {showWaterTable && waterTable?.features?.map((f, i) => {
        const [lng, lat] = f.geometry.coordinates;
        const depth = f.properties.water_table_depth_m;
        return (
          <CircleMarker
            key={`wt-${i}`}
            center={[lat, lng]}
            radius={6}
            pathOptions={{ color: "#0EA5E9", fillColor: "#0EA5E9", fillOpacity: 0.6, weight: 1 }}
          >
            <Popup>
              <strong>{f.properties.name}</strong><br />
              Water table depth: {depth} m
              <br /><span style={{ fontSize: 11, color: "#8FA3B8" }}>Illustrative estimate, not a CGWB measurement.</span>
            </Popup>
          </CircleMarker>
        );
      })}

      {mines.map((m) => (
        <CircleMarker
          key={m.id}
          center={[m.lat, m.lng]}
          radius={m.id === selectedMineId ? 11 : 8}
          pathOptions={{
            color: STATUS_COLOR[m.status] || "#8FA3B8",
            fillColor: STATUS_COLOR[m.status] || "#8FA3B8",
            fillOpacity: 0.9,
            weight: m.id === selectedMineId ? 3 : 1.5,
          }}
          eventHandlers={{ click: () => onSelectMine(m.id) }}
        >
          <Popup>
            <strong>{m.name}</strong><br />
            {m.state}<br />
            Status: {m.status} (mock data)
          </Popup>
        </CircleMarker>
      ))}

      {showMoilReal && moilRealMines && moilRealMines.map((m) => (
        <Marker key={m.name} position={[m.lat, m.lng]} icon={moilIcon}>
          <Popup>
            <strong>{m.name}</strong> (real MOIL mine)<br />
            {m.district}, {m.state}<br />
            Type: {m.type}<br />
            <span style={{ fontSize: 11, color: "#8FA3B8" }}>Location confidence: {m.confidence}</span>
            {m.note && <><br /><span style={{ fontSize: 11 }}>{m.note}</span></>}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
