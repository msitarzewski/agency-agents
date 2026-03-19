"use client";
import { useState } from "react";

const CHANNELS = ["Instagram Post", "Instagram Story", "Facebook Ad", "LinkedIn Post", "Twitter/X Thread", "Email Campaign", "Print/Flyer"];
const TONES = ["Warm & Empowering", "Professional & Expert", "Urgent & Action-Oriented", "Playful & Engaging", "Educational & Informative"];
const GOALS = ["Awareness", "Event Registration", "Lead Generation", "Product Sale", "Community Building", "Brand Authority"];

export default function GeneratorPage() {
  const [form, setForm] = useState({
    channel: CHANNELS[0],
    tone: TONES[0],
    audience: "",
    goal: GOALS[0],
    cta: "",
    extraContext: "",
  });
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generate = async () => {
    setLoading(true);
    setError("");
    setOutput("");
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setOutput(data.copy);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const field = (label: string, key: keyof typeof form, type: "text" | "textarea" | "select", options?: string[]) => (
    <div style={{ marginBottom: 20 }}>
      <label style={{ display: "block", fontWeight: 700, marginBottom: 6, fontSize: 13, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {label}
      </label>
      {type === "select" ? (
        <select value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
          style={{ width: "100%", padding: "10px 14px", border: "1.5px solid #ddd", borderRadius: 8, fontSize: 14, background: "white" }}>
          {options!.map(o => <option key={o}>{o}</option>)}
        </select>
      ) : type === "textarea" ? (
        <textarea value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
          rows={3}
          style={{ width: "100%", padding: "10px 14px", border: "1.5px solid #ddd", borderRadius: 8, fontSize: 14, resize: "vertical" }} />
      ) : (
        <input type="text" value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
          style={{ width: "100%", padding: "10px 14px", border: "1.5px solid #ddd", borderRadius: 8, fontSize: 14 }} />
      )}
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "#FAF7F4", fontFamily: "system-ui, sans-serif" }}>
      {/* REPLACE: Update header colours to match brand */}
      <header style={{ background: "linear-gradient(135deg, #5C2D6E 0%, #C9778A 100%)", color: "white", padding: "40px", textAlign: "center" }}>
        <h1 style={{ fontSize: 32, marginBottom: 8 }}>AI Content Generator</h1>
        {/* REPLACE: Update subtitle with client name */}
        <p style={{ opacity: 0.85 }}>Generate on-brand marketing copy for [CLIENT NAME]</p>
      </header>

      <main style={{ maxWidth: 800, margin: "0 auto", padding: "40px 20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
        <div style={{ background: "white", borderRadius: 16, padding: 32, boxShadow: "0 4px 20px rgba(0,0,0,0.08)" }}>
          <h2 style={{ marginBottom: 24, fontSize: 20 }}>Campaign Brief</h2>
          {field("Channel", "channel", "select", CHANNELS)}
          {field("Tone", "tone", "select", TONES)}
          {field("Target Audience", "audience", "text")}
          {field("Goal", "goal", "select", GOALS)}
          {field("CTA (Call to Action)", "cta", "text")}
          {field("Extra Context (optional)", "extraContext", "textarea")}
          <button onClick={generate} disabled={loading}
            style={{
              width: "100%", padding: "14px", background: "#5C2D6E", color: "white",
              border: "none", borderRadius: 8, fontSize: 15, fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.7 : 1,
            }}>
            {loading ? "Generating..." : "Generate Copy"}
          </button>
          {error && <p style={{ color: "red", marginTop: 12, fontSize: 13 }}>{error}</p>}
        </div>

        <div style={{ background: "white", borderRadius: 16, padding: 32, boxShadow: "0 4px 20px rgba(0,0,0,0.08)" }}>
          <h2 style={{ marginBottom: 24, fontSize: 20 }}>Generated Copy</h2>
          {output ? (
            <>
              <pre style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.7, color: "#333" }}>{output}</pre>
              <button onClick={() => navigator.clipboard.writeText(output)}
                style={{ marginTop: 16, padding: "8px 16px", background: "#F5EDE8", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 13, fontWeight: 700 }}>
                Copy to Clipboard
              </button>
            </>
          ) : (
            <p style={{ color: "#aaa", fontSize: 14 }}>Fill in the brief and click Generate Copy to get started.</p>
          )}
        </div>
      </main>
    </div>
  );
}
