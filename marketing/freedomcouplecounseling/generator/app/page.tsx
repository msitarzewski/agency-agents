"use client";

import { useState, useRef } from "react";
import styles from "./page.module.css";
import MockupCard from "./components/MockupCard";

const CHANNELS = [
  { value: "instagram_post", label: "Instagram Post" },
  { value: "instagram_story", label: "Instagram Story" },
  { value: "facebook_ad", label: "Facebook Ad" },
  { value: "email", label: "Email Campaign" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "twitter", label: "Twitter / X Thread" },
  { value: "tiktok", label: "TikTok" },
];

const CONTENT_TYPES = [
  { value: "service_spotlight", label: "Service Spotlight" },
  { value: "relationship_tip", label: "Relationship Tip / Education" },
  { value: "testimonial", label: "Client Testimonial / Social Proof" },
  { value: "booking_prompt", label: "Book a Session / CTA" },
  { value: "faith_relationship", label: "Faith & Relationship" },
  { value: "premarital", label: "Pre-Marital Counselling" },
];

export default function Home() {
  const [channel, setChannel] = useState("instagram_post");
  const [contentType, setContentType] = useState("service_spotlight");
  const [customContext, setCustomContext] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function generate() {
    if (loading) return;
    setOutput("");
    setLoading(true);
    setCopied(false);

    abortRef.current = new AbortController();

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel, contentType, customContext }),
        signal: abortRef.current.signal,
      });

      if (!res.ok || !res.body) {
        setOutput("[Error: Failed to reach API]");
        setLoading(false);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let result = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        result += decoder.decode(value, { stream: true });
        setOutput(result);
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setOutput("[Error: Request failed]");
      }
    } finally {
      setLoading(false);
    }
  }

  function stop() {
    abortRef.current?.abort();
    setLoading(false);
  }

  async function copyOutput() {
    if (!output) return;
    await navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <main className={styles.main}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.logo}>
            <img
              src="//static.showit.co/400/t6v6SWjZ3RL-qNDvah52ng/shared/freedom_couple_counselling_logo_master_rgb_transparent_bg.png"
              alt="Freedom Couple Counselling"
              className={styles.logoImg}
            />
            <div className={styles.logoText}>
              <div className={styles.logoTitle}>Marketing Generator</div>
              <div className={styles.logoSub}>Freedom Couple Counselling</div>
            </div>
          </div>
          <div className={styles.headerMeta}>
            <span className={styles.pill}>Melbourne</span>
            <span className={styles.pill}>Couples Counselling</span>
            <span className={styles.pill}>Claude AI</span>
          </div>
        </div>
      </header>

      <div className={styles.layout}>
        {/* Sidebar / Controls */}
        <aside className={styles.sidebar}>
          <h2 className={styles.sidebarTitle}>Generate Content</h2>

          <div className={styles.field}>
            <label className={styles.label}>Channel</label>
            <div className={styles.segmentGrid}>
              {CHANNELS.map((c) => (
                <button
                  key={c.value}
                  className={`${styles.segment} ${channel === c.value ? styles.segmentActive : ""}`}
                  onClick={() => setChannel(c.value)}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Content Type</label>
            <div className={styles.segmentGrid}>
              {CONTENT_TYPES.map((ct) => (
                <button
                  key={ct.value}
                  className={`${styles.segment} ${contentType === ct.value ? styles.segmentActive : ""}`}
                  onClick={() => setContentType(ct.value)}
                >
                  {ct.label}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>
              Additional Context <span className={styles.optional}>(optional)</span>
            </label>
            <textarea
              className={styles.textarea}
              rows={4}
              placeholder="E.g. Focus on intercultural couples. Mention a free 15-min discovery call. Target newlyweds specifically."
              value={customContext}
              onChange={(e) => setCustomContext(e.target.value)}
            />
          </div>

          <div className={styles.actions}>
            {!loading ? (
              <button className={styles.btnPrimary} onClick={generate}>
                Generate Content
              </button>
            ) : (
              <button className={styles.btnStop} onClick={stop}>
                Stop Generating
              </button>
            )}
          </div>

          <div className={styles.hint}>
            Powered by Claude claude-opus-4-6 with extended thinking. Copy is generated fresh each time — regenerate for variations.
          </div>
        </aside>

        {/* Output */}
        <section className={styles.outputSection}>
          {!output && !loading && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>♡</div>
              <h3>Ready to create</h3>
              <p>Select a channel and content type, then click Generate Content.</p>
              <p className={styles.emptyNote}>
                Each generation produces platform-optimised copy and a branded asset mockup ready to download.
              </p>
            </div>
          )}

          {(output || loading) && (
            <>
              {/* Marketing copy block */}
              <div className={styles.outputBlock}>
                <div className={styles.outputBlockHeader}>
                  <span className={styles.outputBlockLabel}>
                    {loading && !output ? "Generating…" : "Marketing Copy"}
                  </span>
                  {output && !loading && (
                    <button className={styles.copyBtn} onClick={copyOutput}>
                      {copied ? "Copied!" : "Copy"}
                    </button>
                  )}
                </div>
                <pre className={styles.outputText}>{output}</pre>
                {loading && <span className={styles.cursor} />}
              </div>

              {/* Brand mockup — auto-shown once generation is done */}
              {!loading && output && (
                <div className={`${styles.outputBlock} ${styles.outputBlockImage}`}>
                  <div className={styles.outputBlockHeader}>
                    <span className={styles.outputBlockLabel}>Asset Mockup</span>
                  </div>
                  <div style={{ padding: "20px 18px" }}>
                    <MockupCard channel={channel} contentType={contentType} output={output} />
                  </div>
                </div>
              )}

              {!loading && output && (
                <div className={styles.regenBar}>
                  <button className={styles.btnSecondary} onClick={generate}>
                    Regenerate Variation
                  </button>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}
