import { useRef, useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X } from "lucide-react";
import { api } from "../api";

const REQUIRED_COLUMNS = ["mine_id", "period", "planned_tonnes", "actual_tonnes"];

export default function UploadDataPage() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef(null);

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
      const res = await api.uploadProductionCSV(file);
      setResult(res);
      setStatus("success");
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
    <div style={{ maxWidth: 720 }}>
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 15, marginBottom: 4 }}>Upload Production Data</h3>
        <p style={{ color: "var(--text-soft)", fontSize: 13, marginBottom: 16 }}>
          Upload a CSV of planned vs. actual tonnage. Rows are appended to production data
          and immediately reflected on the Dashboard and Reports.
        </p>

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
            Required columns: {REQUIRED_COLUMNS.join(", ")}
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
          {status === "loading" ? "Uploading…" : "Upload & Process"}
        </button>

        {status === "success" && result && (
          <div style={{
            display: "flex", alignItems: "flex-start", gap: 8, marginTop: 14,
            padding: "10px 14px", borderRadius: 8, background: "var(--accent-green-soft)",
          }}>
            <CheckCircle2 size={18} color="var(--accent-green)" style={{ flexShrink: 0, marginTop: 1 }} />
            <div style={{ fontSize: 13 }}>
              <div style={{ color: "var(--accent-green)", fontWeight: 600 }}>
                {result.rows_added} row{result.rows_added === 1 ? "" : "s"} added successfully
              </div>
              {result.rows_skipped > 0 && (
                <div style={{ color: "var(--text-soft)", marginTop: 2 }}>
                  {result.rows_skipped} row{result.rows_skipped === 1 ? "" : "s"} skipped due to invalid data.
                </div>
              )}
              {result.errors?.length > 0 && (
                <ul style={{ marginTop: 6, paddingLeft: 18, color: "var(--text-soft)", fontSize: 12 }}>
                  {result.errors.map((err, i) => <li key={i}>{err}</li>)}
                </ul>
              )}
            </div>
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
