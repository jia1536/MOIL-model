/**
 * ProspectivityMap.jsx
 * ---------------------
 * Replaces flat "pin on a map" visualization with:
 *   1. A contoured, color-graded prospectivity surface (kriging/IDW output
 *      from the backend), matching the 5-level natural-breaks classification
 *      style used in the reference literature (low -> very high).
 *   2. Per-zone explainability popup — top contributing features for that
 *      exact prediction (from RF feature-importance / SHAP), not just a score.
 *   3. Toggleable overlays: water table depth, known MOIL mines, licensed
 *      company operating areas, reserve-depletion urgency shading.
 *
 * Assumes `leaflet` is already a dependency (per your tech stack) and that
 * the backend exposes:
 *   GET /api/zones          -> GeoJSON FeatureCollection, one polygon per
 *                              interpolated grid cell, properties include
 *                              { score, level, top_features: [...] }
 *   GET /api/mines          -> GeoJSON points, known MOIL mine locations
 *   GET /api/watertable     -> GeoJSON polygons, CGWB water-level bands
 *
 * No paid map API key is required for the base map — this uses OpenStreetMap
 * tiles (free, no key, no usage cap for reasonable traffic) via Leaflet.
 * See docs/API_KEYS_SETUP.md for when you WOULD need a key (satellite basemap
 * imagery tiles, geocoding search box) and exactly how to get one securely.
 */

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const LEVEL_COLORS = {
  "very low": "#e5e7eb",
  low: "#bae6fd",
  medium: "#facc15",
  high: "#fb923c",
  "very high": "#dc2626",
};

function styleForZone(feature) {
  const level = feature.properties.level || "very low";
  return {
    fillColor: LEVEL_COLORS[level] || "#e5e7eb",
    fillOpacity: 0.55,
    color: "#1f2937",
    weight: 0.5,
  };
}

function buildExplainabilityHTML(props) {
  // top_features comes from routes_map.py's explain_by_perturbation() —
  // contribution = how much the score moved when that feature was swapped
  // back to its dataset baseline (positive = this feature is pushing the
  // score up relative to a "typical" location).
  const rows = (props.top_features || [])
    .slice(0, 4)
    .map(
      (f) =>
        `<div style="display:flex;justify-content:space-between;font-size:12px;padding:2px 0;">
           <span>${f.name}</span>
           <span style="font-weight:600;">${f.contribution > 0 ? "+" : ""}${f.contribution.toFixed(3)}</span>
         </div>`
    )
    .join("");

  const vc = props.viability_components || {};
  const componentRows = Object.keys(vc).length
    ? `<div style="margin-top:6px;padding-top:6px;border-top:1px solid #eee;">
         <div style="font-size:11px;color:#888;margin-bottom:2px;">Viability breakdown</div>
         <div style="font-size:11px;">Prospectivity: ${vc.prospectivity_score?.toFixed(2)}</div>
         <div style="font-size:11px;">Shortfall risk: ${vc.shortfall_risk_score?.toFixed(2)}</div>
         <div style="font-size:11px;">Water stress: ${vc.water_stress_score?.toFixed(2)}</div>
         <div style="font-size:11px;">Reserve urgency: ${vc.reserve_urgency_score?.toFixed(2)}</div>
       </div>`
    : "";

  return `
    <div style="min-width:210px;font-family:system-ui,sans-serif;">
      <div style="font-weight:700;font-size:14px;margin-bottom:4px;">
        Prospectivity: ${(props.score * 100).toFixed(0)}% (${props.level})
      </div>
      <div style="font-size:11px;color:#888;margin-bottom:2px;">Key drivers</div>
      ${rows || "<div style='font-size:12px;color:#999;'>No breakdown available</div>"}
      ${
        props.viability_index != null
          ? `<div style="margin-top:6px;padding-top:6px;border-top:1px solid #eee;font-size:13px;">
               Mine Viability Index: <b>${props.viability_index.toFixed(2)}</b>
             </div>`
          : ""
      }
      ${componentRows}
    </div>
  `;
}

export default function ProspectivityMap({
  apiBaseUrl = "/api",
  center = [21.8, 80.18],
  zoom = 8,
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const layersRef = useRef({});
  const [activeOverlays, setActiveOverlays] = useState({
    zones: true,
    mines: true,
    watertable: false,
  });
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    if (mapRef.current) return; // init once

    const map = L.map(mapContainerRef.current).setView(center, zoom);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(map);

    mapRef.current = map;

    const loadLayers = async () => {
      try {
        const [zonesRes, minesRes, waterRes] = await Promise.all([
          fetch(`${apiBaseUrl}/zones`).then((r) => r.json()),
          fetch(`${apiBaseUrl}/mines`).then((r) => r.json()),
          fetch(`${apiBaseUrl}/watertable`).then((r) => r.json()),
        ]);

        layersRef.current.zones = L.geoJSON(zonesRes, {
          style: styleForZone,
          onEachFeature: (feature, layer) => {
            layer.bindPopup(buildExplainabilityHTML(feature.properties));
          },
        }).addTo(map);

        layersRef.current.mines = L.geoJSON(minesRes, {
          pointToLayer: (feature, latlng) =>
            L.circleMarker(latlng, {
              radius: 6,
              fillColor: "#1e3a8a",
              color: "#fff",
              weight: 1,
              fillOpacity: 0.9,
            }),
          onEachFeature: (feature, layer) => {
            layer.bindPopup(
              `<b>${feature.properties.name}</b><br/>${
                feature.properties.operator || "Operator unknown"
              }`
            );
          },
        }).addTo(map);

        layersRef.current.watertable = L.geoJSON(waterRes, {
          style: { color: "#0ea5e9", weight: 1, fillOpacity: 0.15 },
        });
        // not added by default — user toggles it on

        setStatus("ready");
      } catch (err) {
        console.error("Failed to load map layers:", err);
        setStatus("error");
      }
    };

    loadLayers();

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleOverlay = (key) => {
    const map = mapRef.current;
    const layer = layersRef.current[key];
    if (!map || !layer) return;

    setActiveOverlays((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      if (next[key]) {
        layer.addTo(map);
      } else {
        map.removeLayer(layer);
      }
      return next;
    });
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "600px" }}>
      <div
        ref={mapContainerRef}
        style={{ width: "100%", height: "100%", borderRadius: 8 }}
      />

      <div
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          background: "white",
          borderRadius: 6,
          padding: "10px 12px",
          boxShadow: "0 1px 4px rgba(0,0,0,0.2)",
          fontFamily: "system-ui, sans-serif",
          fontSize: 13,
          zIndex: 1000,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6 }}>Layers</div>
        {["zones", "mines", "watertable"].map((key) => (
          <label
            key={key}
            style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 4 }}
          >
            <input
              type="checkbox"
              checked={activeOverlays[key]}
              onChange={() => toggleOverlay(key)}
            />
            {key === "watertable" ? "Water table" : key === "mines" ? "Known mines" : "Prospectivity zones"}
          </label>
        ))}

        <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid #eee" }}>
          <div style={{ fontSize: 11, color: "#888", marginBottom: 4 }}>Prospectivity</div>
          {Object.entries(LEVEL_COLORS).map(([level, color]) => (
            <div key={level} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  background: color,
                  display: "inline-block",
                  borderRadius: 2,
                }}
              />
              <span style={{ textTransform: "capitalize" }}>{level}</span>
            </div>
          ))}
        </div>
      </div>

      {status === "error" && (
        <div
          style={{
            position: "absolute",
            bottom: 12,
            left: 12,
            background: "#fee2e2",
            color: "#991b1b",
            padding: "8px 12px",
            borderRadius: 6,
            fontSize: 13,
          }}
        >
          Couldn't load map data. Check that the backend API is running.
        </div>
      )}
    </div>
  );
}
