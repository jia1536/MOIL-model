import { useRef, useState, useEffect, Fragment } from "react";
import { Send, Wrench } from "lucide-react";
import { api } from "../api";

const SUGGESTIONS = [
  "Which mines are at high risk of a production shortfall?",
  "Compare India, South Africa and Australia's manganese reserves",
  "What's the remaining reserve and annual production for Madhya Pradesh?",
];

// Small, dependency-free renderer for the light markdown a chat model tends
// to use (**bold**, "- " bullet lines). Not a full markdown parser, just
// enough so a reply never shows raw asterisks or literal "- " bullets.
function renderInline(text, keyPrefix) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</strong>
      : <Fragment key={`${keyPrefix}-${i}`}>{part}</Fragment>
  );
}

function MessageContent({ text }) {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => {
        const bullet = line.match(/^\s*[-*]\s+(.*)/);
        if (bullet) {
          return (
            <div key={i} style={{ display: "flex", gap: 6, marginTop: i > 0 ? 2 : 0 }}>
              <span>&#8226;</span>
              <span>{renderInline(bullet[1], i)}</span>
            </div>
          );
        }
        return <div key={i}>{renderInline(line, i)}</div>;
      })}
    </>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState([]); // [{role, content, toolsUsed?}]
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text) {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content }]);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const res = await api.chat(content, history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply, toolsUsed: res.tools_used }]);
    } catch (e) {
      setError(e.message || "Chat request failed. Is the backend running with GROQ_API_KEY set?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 760, height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <h3 style={{ fontSize: 15, marginBottom: 4 }}>Ask the assistant</h3>
        <p style={{ color: "var(--text-soft)", fontSize: 13, marginBottom: 16 }}>
          Tool-calling chatbot with live access to mine data, forecasts, reserves and country comparisons.
        </p>

        <div style={{ flex: 1, overflowY: "auto", minHeight: 200, marginBottom: 12 }}>
          {messages.length === 0 && (
            <div>
              <p style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 8 }}>Try asking:</p>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  style={{
                    display: "block", textAlign: "left", width: "100%", padding: "10px 12px", marginBottom: 8,
                    borderRadius: 8, border: "1px solid var(--border)", background: "var(--page-bg)",
                    color: "var(--text)", fontSize: 13,
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} style={{ marginBottom: 14, display: "flex", flexDirection: "column", alignItems: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{
                maxWidth: "80%", padding: "10px 14px", borderRadius: 12, fontSize: 13,
                background: m.role === "user" ? "var(--primary-blue)" : "var(--page-bg)",
                color: m.role === "user" ? "white" : "var(--text)",
              }}>
                <MessageContent text={m.content} />
              </div>
              {m.toolsUsed?.length > 0 && (
                <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--text-soft)", marginTop: 4 }}>
                  <Wrench size={11} /> {m.toolsUsed.join(", ")}
                </div>
              )}
            </div>
          ))}

          {loading && <p style={{ fontSize: 13, color: "var(--text-soft)" }}>Thinking…</p>}
          {error && <p style={{ fontSize: 13, color: "var(--danger-red)" }}>{error}</p>}
          <div ref={bottomRef} />
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") send(); }}
            placeholder="Ask about mines, forecasts, reserves…"
            style={{
              flex: 1, padding: "10px 14px", borderRadius: 8, border: "1px solid var(--border)",
              fontSize: 13, fontFamily: "var(--font)", background: "var(--page-bg)", color: "var(--text)",
            }}
          />
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            style={{
              display: "flex", alignItems: "center", gap: 6, padding: "10px 16px", borderRadius: 8,
              background: loading || !input.trim() ? "var(--border)" : "linear-gradient(135deg, #2563EB, #1D4ED8)",
              color: loading || !input.trim() ? "var(--text-soft)" : "white", fontWeight: 600, fontSize: 13,
            }}
          >
            <Send size={14} /> Send
          </button>
        </div>
      </div>
    </div>
  );
}
