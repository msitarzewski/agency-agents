"use client";

import { useState, useRef } from "react";
import styles from "./page.module.css";

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
  const [copySection, setCopySection] = useState<"copy" | "image" | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const hasSections = output.includes("--- IMAGE PROMPT ---");
  const copyPart = hasSections ? output.split("--- IMAGE PROMPT ---")[0]?.trim() : output;
  const imagePart = hasSections ? output.split("--- IMAGE PROMPT ---")[1]?.trim() : "";

  async function generateImageFromPrompt(prompt: string, chan: string) {
    setImageLoading(true);
    setImageError(null);
    setGeneratedImage(null);

    try {
      const res = await fetch("/api/generate-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, channel: chan }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Image generation failed");
      setGeneratedImage(data.url);
    } catch (err) {
      setImageError((err as Error).message ?? "Failed to generate image");
    } finally {
      setImageLoading(false);
    }
  }

  async function generate() {
    if (loading) return;
    setOutput("");
    setLoading(true);
    setCopied(false);
    setGeneratedImage(null);
    setImageError(null);

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
        const chunk = decoder.decode(value, { stream: true });
        result += chunk;
        setOutput(result);
      }

      // Auto-generate image once content is complete
      if (result.includes("--- IMAGE PROMPT ---")) {
        const extractedPrompt = result.split("--- IMAGE PROMPT ---")[1]?.trim();
        if (extractedPrompt) {
          await generateImageFromPrompt(extractedPrompt, channel);
        }
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

  async function copySectionText(section: "copy" | "image") {
    const text = section === "copy" ? copyPart : imagePart;
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopySection(section);
    setTimeout(() => setCopySection(null), 2000);
  }

  async function generateImage() {
    if (!imagePart || imageLoading) return;
    await generateImageFromPrompt(imagePart, channel);
  }

  async function downloadImage() {
    if (!generatedImage) return;
    const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(generatedImage)}`;
    const a = document.createElement("a");
    a.href = proxyUrl;
    a.download = `fcc-image-${Date.now()}.png`;
    a.click();
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
                Each generation includes platform-optimised copy and an AI image prompt — then generate the actual image with one click.
              </p>
            </div>
          )}

          {(output || loading) && (
            <>
              {hasSections ? (
                <>
                  <div className={styles.outputBlock}>
                    <div className={styles.outputBlockHeader}>
                      <span className={styles.outputBlockLabel}>Marketing Copy</span>
                      <button
                        className={styles.copyBtn}
                        onClick={() => copySectionText("copy")}
                      >
                        {copySection === "copy" ? "Copied!" : "Copy"}
                      </button>
                    </div>
                    <pre className={styles.outputText}>{copyPart}</pre>
                  </div>

                  {imagePart && (
                    <div className={`${styles.outputBlock} ${styles.outputBlockImage}`}>
                      <div className={styles.outputBlockHeader}>
                        <span className={styles.outputBlockLabel}>Generated Image</span>
                        <div className={styles.headerBtns}>
                          {!imageLoading ? (
                            <button
                              className={styles.btnGenerateImage}
                              onClick={generateImage}
                            >
                              {generatedImage ? "Regenerate Image" : "Generate Image"}
                            </button>
                          ) : (
                            <button className={styles.btnGenerateImage} disabled>
                              Generating…
                            </button>
                          )}
                        </div>
                      </div>

                      {imageLoading && (
                        <div className={styles.imageLoadingState}>
                          <div className={styles.imageSpinner} />
                          <p>Generating your image with DALL·E 3… this takes ~15 seconds</p>
                        </div>
                      )}

                      {imageError && (
                        <div className={styles.imageError}>
                          {imageError}
                        </div>
                      )}

                      {generatedImage && !imageLoading && (
                        <div className={styles.imageResult}>
                          <img
                            src={generatedImage}
                            alt="AI-generated marketing image"
                            className={styles.generatedImg}
                          />
                          <div className={styles.imageActions}>
                            <button className={styles.btnDownload} onClick={downloadImage}>
                              Download Image
                            </button>
                            <button className={styles.btnSecondary} onClick={generateImage}>
                              Regenerate
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className={styles.outputBlock}>
                  <div className={styles.outputBlockHeader}>
                    <span className={styles.outputBlockLabel}>
                      {loading ? "Generating…" : "Output"}
                    </span>
                    {output && (
                      <button className={styles.copyBtn} onClick={copyOutput}>
                        {copied ? "Copied!" : "Copy All"}
                      </button>
                    )}
                  </div>
                  <pre className={styles.outputText}>{output}</pre>
                  {loading && <span className={styles.cursor} />}
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
