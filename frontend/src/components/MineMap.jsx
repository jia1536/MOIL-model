import { MapContainer, TileLayer, CircleMarker, Marker, Popup, GeoJSON } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const STATUS_COLOR = { active: "#2563EB", prospective: "#F59E0B" };

function zoneStyle(feature) {
  const score = feature.properties.prospectivity_score;
  const color = score > 0.6 ? "#EF4444" : score > 0.4 ? "#F59E0B" : "#10B981";
  return { color, weight: 1, fillColor: color, fillOpacity: 0.35 };
}

const moilIcon = L.divIcon({
  className: "",
  html: `<div style="width:14px;height:14px;background:#F59E0B;border:2px solid #F8FAFC;border-radius:3px;transform:rotate(45deg);box-shadow:0 0 0 2px #F59E0B55;"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

export default function MineMap({ mines, zones, moilRealMines, selectedMineId, onSelectMine, showMoilReal }) {
  return (
    <MapContainer
      center={[20.5, 80.5]}
      zoom={5}
      scrollWheelZoom={true}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; OpenStreetMap contributors, &copy; CARTO'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      />
      {zones && <GeoJSON data={zones} style={zoneStyle} />}

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
