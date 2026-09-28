import { useRef, useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X, Download } from "lucide-react";
import { api } from "../api";

const MODE_INFO = {
  score: {
    title: "Score coordinates",
    description:
      "Upload lat/lng points and each one is run through the live pipeline (satellite, geology, model, viability). Nothing on the server is changed, this is read-only scoring.",
    columns: ["lat", "lng"],
  },
  replace: {
    title: "Replace mine list",
    description:
      "Upload a full replacement mine list. This becomes the live MINES list for every endpoint immediately, use with care.",
    columns: ["name", "state", "lat", "lng", "status", "type"],
  },
};

export default function UploadDataPage({ onMinesReplaced }) {
  const [mode, setMode] = useState("score");
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [useRealSatellite, setUseRealSatellite] = useState(false);
  const [persist, setPersist] = useState(true);
  const inputRef = useRef(null);

  const info = MODE_INFO[mode];

  function switchMode(newMode) {
    setMode(newMode);
    setFile(null);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
    if (inputRef.current) inputRef.current.value = "";
  }

  function pickFile(f) {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".csv")) {
      setStatus("error");
      setErrorMsg("Please select a .csv file.");
      return;
    }
    setFile(f);
    setStatus("idle");
    setResult(null);
    setErrorMsg("");
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    pickFile(e.dataTransfer.files?.[0]);
  }

  async function handleUpload() {
    if (!file) return;
    setStatus("loading");
    setErrorMsg("");
    try {
      const res = await api.uploadCsv(file, { mode, useRealSatellite, persist });
      setResult(res);
      setStatus("success");
      if (mode === "replace" && onMinesReplaced) onMinesReplaced(res.mines);
    } catch (e) {
      setErrorMsg(e.message || "Upload failed. Is the backend running on port 8000?");
      setStatus("error");
    }
  }

  function reset() {
    setFile(null);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div style={{ maxWidth: 820 }}>
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 15, marginBottom: 4 }}>Upload CSV</h3>

        <div style={{ display: "flex", gap: 8, margin: "14px 0" }}>
          {Object.entries(MODE_INFO).map(([key, m]) => (
            <button
              key={key}
              onClick={() => switchMode(key)}
              style={{
                padding: "8px 14px", fontSize: 13, fontWeight: 600, borderRadius: 8,
                background: mode === key ? "var(--primary-blue)" : "var(--page-bg)",
                color: mode === key ? "white" : "var(--text-soft)",
                border: `1px solid ${mode === key ? "var(--primary-blue)" : "var(--border)"}`,
              }}
            >
              {m.title}
            </button>
          ))}
        </div>

        <p style={{ color: "var(--text-soft)", fontSize: 13, marginBottom: 12 }}>{info.description}</p>

        <a
          href={api.getUploadTemplateUrl(mode)}
          style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--primary-blue)", marginBottom: 16 }}
        >
          <Download size={13} /> Download {mode} template CSV
        </a>

        {mode === "score" && (
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, marginBottom: 14, cursor: "pointer" }}>
            <input type="checkbox" checked={useRealSatellite} onChange={(e) => setUseRealSatellite(e.target.checked)} />
            Use real satellite data per row (slower, live Earth Engine calls; off uses the fast geological-prior path)
          </label>
        )}
        {mode === "replace" && (
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, marginBottom: 14, cursor: "pointer" }}>
            <input type="checkbox" checked={persist} onChange={(e) => setPersist(e.target.checked)} />
            Persist to disk (survives a server restart)
          </label>
        )}

        <label
          htmlFor="csv-upload-input"
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          style={{
            display: "block",
            textAlign: "center",
            padding: "40px 20px",
            borderRadius: 12,
            border: `2px dashed ${dragActive ? "var(--primary-blue)" : "var(--border)"}`,
            background: dragActive ? "var(--primary-blue-soft)" : "var(--page-bg)",
            cursor: "pointer",
            transition: "border-color 0.15s, background 0.15s",
          }}
        >
          <UploadCloud size={32} color={dragActive ? "var(--primary-blue)" : "var(--text-soft)"} style={{ margin: "0 auto" }} />
          <p style={{ fontSize: 13, color: "var(--text)", marginTop: 10, fontWeight: 500 }}>
            Click to select a CSV file, or drag one here
          </p>
          <p style={{ fontSize: 11, color: "var(--text-soft)", marginTop: 4 }}>
            Required columns: {info.columns.join(", ")}
          </p>
          <input
            id="csv-upload-input"
            ref={inputRef}
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
        </label>

        {file && (
          <div style={{
            display: "flex", alignItems: "center", gap: 10, marginTop: 14,
            padding: "10px 14px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--card-bg)",
          }}>
            <FileText size={18} color="var(--primary-blue)" />
            <span style={{ fontSize: 13, fontWeight: 500, flex: 1 }}>{file.name}</span>
            <span style={{ fontSize: 11, color: "var(--text-soft)" }}>{(file.size / 1024).toFixed(1)} KB</span>
            <button
              onClick={reset}
              style={{ background: "none", padding: 4, display: "flex", color: "var(--text-soft)" }}
              aria-label="Remove file"
            >
              <X size={16} />
            </button>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || status === "loading"}
          style={{
            marginTop: 16,
            background: !file || status === "loading" ? "var(--border)" : "linear-gradient(135deg, #2563EB, #1D4ED8)",
            color: !file || status === "loading" ? "var(--text-soft)" : "white",
            padding: "11px 22px",
            fontWeight: 600,
            fontSize: 13,
            borderRadius: 8,
            boxShadow: !file || status === "loading" ? "none" : "0 2px 8px rgba(37,99,235,0.35)",
            cursor: !file || status === "loading" ? "not-allowed" : "pointer",
          }}
        >
          {status === "loading" ? (mode === "score" ? "Scoring…" : "Uploading…") : "Upload & Process"}
        </button>

        {status === "success" && result && mode === "score" && (
          <div style={{ marginTop: 16 }}>
            <div style={{
              display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 12,
              padding: "10px 14px", borderRadius: 8, background: "var(--accent-green-soft)",
            }}>
              <CheckCircle2 size={18} color="var(--accent-green)" style={{ flexShrink: 0, marginTop: 1 }} />
              <div style={{ fontSize: 13 }}>
                <div style={{ color: "var(--accent-green)", fontWeight: 600 }}>
                  {result.rows_scored} of {result.rows_received} row{result.rows_received === 1 ? "" : "s"} scored
                </div>
                {result.rows_failed > 0 && (
                  <div style={{ color: "var(--text-soft)", marginTop: 2 }}>
                    {result.rows_failed} row{result.rows_failed === 1 ? "" : "s"} failed. See below.
                  </div>
                )}
              </div>
            </div>

            {result.results?.length > 0 && (
              <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 8 }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr style={{ background: "var(--page-bg)", textAlign: "left" }}>
                      <th style={{ padding: 8 }}>Row</th>
                      <th style={{ padding: 8 }}>Lat, Lng</th>
                      <th style={{ padding: 8 }}>Score</th>
                      <th style={{ padding: 8 }}>Level</th>
                      <th style={{ padding: 8 }}>Viability</th>
                      <th style={{ padding: 8 }}>Nearest mine</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.map((r) => (
                      <tr key={r.row} style={{ borderTop: "1px solid var(--border)" }}>
                        <td style={{ padding: 8 }}>{r.row}</td>
                        <td style={{ padding: 8 }}>{r.lat.toFixed(3)}, {r.lng.toFixed(3)}</td>
                        <td style={{ padding: 8, fontWeight: 600 }}>{r.prospectivity_score}</td>
                        <td style={{ padding: 8 }}>{r.level}</td>
                        <td style={{ padding: 8 }}>{r.viability_index}</td>
                        <td style={{ padding: 8 }}>{r.nearest_mine}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {result.errors?.length > 0 && (
              <ul style={{ marginTop: 10, paddingLeft: 18, color: "var(--danger-red)", fontSize: 12 }}>
                {result.errors.map((err, i) => <li key={i}>Row {err.row}: {err.error}</li>)}
              </ul>
            )}
          </div>
        )}

        {status === "success" && result && mode === "replace" && (
          <div style={{ marginTop: 16 }}>
            <div style={{
              display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 12,
              padding: "10px 14px", borderRadius: 8, background: "var(--accent-green-soft)",
            }}>
              <CheckCircle2 size={18} color="var(--accent-green)" style={{ flexShrink: 0, marginTop: 1 }} />
              <div style={{ fontSize: 13 }}>
                <div style={{ color: "var(--accent-green)", fontWeight: 600 }}>
                  Mine list replaced: {result.previous_mine_count} → {result.new_mine_count} mines
                  {result.persisted_to_disk ? " (persisted to disk)" : " (in-memory only)"}
                </div>
              </div>
            </div>
            {result.note && (
              <p style={{ fontSize: 12, color: "var(--warning-orange)", background: "var(--warning-orange-soft)", padding: "10px 14px", borderRadius: 8 }}>
                {result.note}
              </p>
            )}
          </div>
        )}

        {status === "error" && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginTop: 14,
            padding: "10px 14px", borderRadius: 8, background: "var(--danger-red-soft)",
          }}>
            <AlertCircle size={18} color="var(--danger-red)" />
            <span style={{ fontSize: 13, color: "var(--danger-red)" }}>{errorMsg}</span>
          </div>
        )}
      </div>
    </div>
  );
}
