"use client";

import { useRef } from "react";

interface Props {
  channel: string;
  contentType: string;
  output: string;
}

const LOGO = "https://static.showit.co/400/t6v6SWjZ3RL-qNDvah52ng/shared/freedom_couple_counselling_logo_master_rgb_transparent_bg.png";

const F = "#1A3C2A"; // forest
const S = "#4A7C5E"; // sage
const T = "#C4714A"; // terra
const M = "#7A9E85"; // moss
const CH = "#2D2D2D"; // charcoal

const GRADIENTS: Record<string, Record<string, string>> = {
  instagram_post: {
    service_spotlight: `linear-gradient(135deg, ${F} 0%, ${S} 100%)`,
    relationship_tip:  `linear-gradient(135deg, ${S} 0%, ${M} 100%)`,
    testimonial:       `linear-gradient(135deg, ${S} 0%, ${M} 100%)`,
    booking_prompt:    `linear-gradient(135deg, ${T} 0%, ${F} 100%)`,
    faith_relationship:`linear-gradient(135deg, ${CH} 0%, ${F} 100%)`,
    premarital:        `linear-gradient(135deg, ${T} 0%, ${S} 100%)`,
    _default:          `linear-gradient(135deg, ${F} 0%, ${S} 100%)`,
  },
  instagram_story: {
    service_spotlight: `linear-gradient(180deg, ${F} 0%, ${S} 100%)`,
    testimonial:       `linear-gradient(180deg, ${T} 0%, ${F} 100%)`,
    booking_prompt:    `linear-gradient(180deg, ${F} 0%, ${T} 100%)`,
    _default:          `linear-gradient(180deg, ${T} 0%, ${F} 100%)`,
  },
  facebook_ad: {
    _default: `linear-gradient(135deg, ${F} 0%, ${S} 100%)`,
    booking_prompt: `linear-gradient(135deg, ${T} 0%, ${F} 100%)`,
  },
  linkedin: {
    _default: `linear-gradient(135deg, ${CH} 0%, ${F} 100%)`,
  },
  twitter: {
    _default: `linear-gradient(135deg, ${F} 0%, ${T} 100%)`,
  },
  tiktok: {
    _default: `linear-gradient(180deg, ${CH} 0%, ${T} 100%)`,
  },
  email: {
    _default: `linear-gradient(135deg, ${F} 0%, ${S} 100%)`,
  },
};

function getGradient(channel: string, contentType: string): string {
  const map = GRADIENTS[channel] ?? GRADIENTS.instagram_post;
  return map[contentType] ?? map._default ?? `linear-gradient(135deg, ${F} 0%, ${S} 100%)`;
}

function clean(s: string) {
  return s.replace(/\*\*/g, "").replace(/\*/g, "").replace(/^[-•]\s+/, "").trim();
}

function parseCopy(text: string) {
  const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
  const hashtagLines = lines.filter(l => l.startsWith("#"));
  const hashtags = hashtagLines.join(" ").slice(0, 220);

  const contentLines = lines.filter(l => !l.startsWith("#")).map(clean).filter(Boolean);

  let headline = "";
  const captionLines: string[] = [];

  for (const line of contentLines) {
    if (!headline) {
      const quoteMatch = line.match(/"([^"]{10,100})"/);
      if (quoteMatch) {
        headline = `"${quoteMatch[1]}"`;
      } else if (line.length <= 90) {
        headline = line;
      } else {
        headline = line.slice(0, 88) + "…";
      }
    } else {
      captionLines.push(line);
    }
  }

  const caption = captionLines.slice(0, 5).join("\n\n");
  return { headline, caption, hashtags };
}

export default function MockupCard({ channel, contentType, output }: Props) {
  const mockupRef = useRef<HTMLDivElement>(null);
  const gradient = getGradient(channel, contentType);
  const { headline, caption, hashtags } = parseCopy(output);

  async function handleDownload() {
    if (!mockupRef.current) return;
    // Use browser's built-in canvas API via a hidden iframe print
    const html = mockupRef.current.outerHTML;
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`<!DOCTYPE html><html><head>
      <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400;1,700&family=Lato:wght@400;700;900&display=swap" rel="stylesheet"/>
      <style>body{margin:0;padding:20px;background:#F4EBD7;display:inline-block;}@media print{body{padding:0;}}</style>
    </head><body>${html}</body></html>`);
    win.document.close();
    setTimeout(() => { win.print(); }, 800);
  }

  return (
    <div style={{ fontFamily: "'Lato', sans-serif" }}>
      <link
        href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400;1,700&family=Lato:wght@400;700;900&display=swap"
        rel="stylesheet"
      />
      <div ref={mockupRef}>
        {channel === "instagram_post" && (
          <IGPost gradient={gradient} headline={headline} caption={caption} hashtags={hashtags} />
        )}
        {channel === "instagram_story" && (
          <IGStory gradient={gradient} headline={headline} caption={caption} />
        )}
        {(channel === "facebook_ad" || channel === "linkedin") && (
          <FBCard gradient={gradient} headline={headline} caption={caption} isLinkedIn={channel === "linkedin"} />
        )}
        {(channel === "twitter" || channel === "tiktok") && (
          <TweetCard gradient={gradient} headline={headline} caption={caption} isTikTok={channel === "tiktok"} />
        )}
        {channel === "email" && (
          <EmailCard gradient={gradient} headline={headline} caption={caption} />
        )}
      </div>
      <div style={{ marginTop: 12, display: "flex", justifyContent: "flex-end" }}>
        <button
          onClick={handleDownload}
          style={{
            background: "transparent",
            border: "1px solid #CCAED0",
            color: "#B37D00",
            borderRadius: 6,
            padding: "6px 16px",
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            cursor: "pointer",
          }}
        >
          Download PNG
        </button>
      </div>
    </div>
  );
}

// ── Instagram Post ─────────────────────────────────────────────────────────────
function IGPost({ gradient, headline, caption, hashtags }: {
  gradient: string; headline: string; caption: string; hashtags: string;
}) {
  return (
    <div style={{
      background: "white", borderRadius: 12, overflow: "hidden",
      boxShadow: "0 4px 20px rgba(0,0,0,0.1)", maxWidth: 400,
    }}>
      {/* Header */}
      <div style={{ padding: "10px 14px", display: "flex", alignItems: "center", gap: 10 }}>
        <img src={LOGO} alt="FCC" style={{ height: 32, width: "auto", flexShrink: 0 }} />
        <div style={{ marginLeft: "auto", fontSize: 18, color: "#999" }}>···</div>
      </div>

      {/* Image area */}
      <div style={{
        width: "100%", aspectRatio: "1/1", background: gradient,
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 32, textAlign: "center",
      }}>
        <div>
          <div style={{
            fontFamily: "'Playfair Display', serif", fontStyle: "italic",
            color: "white", fontSize: "clamp(17px, 4vw, 24px)", lineHeight: 1.45,
          }}>{headline}</div>
          <div style={{
            color: "rgba(255,255,255,0.75)", fontSize: 12, marginTop: 10,
            fontStyle: "normal", textTransform: "uppercase", letterSpacing: "0.08em",
          }}>Freedom Couple Counselling</div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ padding: "10px 14px 6px", display: "flex", gap: 14 }}>
        <span style={{ fontSize: 22 }}>🤍</span>
        <span style={{ fontSize: 22 }}>💬</span>
        <span style={{ fontSize: 22 }}>✈️</span>
        <span style={{ fontSize: 22, marginLeft: "auto" }}>🔖</span>
      </div>

      {/* Caption */}
      <div style={{ padding: "0 14px 8px", fontSize: 13, lineHeight: 1.55, color: "#262626" }}>
        <span style={{ fontWeight: 700 }}>freedomcouplecounselling</span>{" "}
        {caption}
      </div>

      {/* Hashtags */}
      {hashtags && (
        <div style={{ padding: "0 14px 10px", fontSize: 12, color: "#00376b", lineHeight: 1.6 }}>
          {hashtags}
        </div>
      )}

      {/* Comment stub */}
      <div style={{ padding: "0 14px 12px", fontSize: 12, color: "#8e8e8e" }}>
        View all comments
      </div>
    </div>
  );
}

// ── Instagram Story ────────────────────────────────────────────────────────────
function IGStory({ gradient, headline, caption }: {
  gradient: string; headline: string; caption: string;
}) {
  return (
    <div style={{
      width: 270, height: 480, borderRadius: 20, overflow: "hidden",
      background: gradient, display: "flex", flexDirection: "column",
      justifyContent: "space-between", padding: 20,
      boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
    }}>
      {/* Top */}
      <div>
        <div style={{ display: "flex", gap: 3, marginBottom: 8 }}>
          {[1,2,3,4,5].map(i => (
            <div key={i} style={{
              flex: 1, height: 2, borderRadius: 1,
              background: i === 1 ? "white" : "rgba(255,255,255,0.4)",
            }} />
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <img src={LOGO} alt="FCC" style={{ height: 28, width: "auto" }} />
          <div style={{ color: "rgba(255,255,255,0.6)", fontSize: 11 }}>Now</div>
        </div>
      </div>

      {/* Content */}
      <div style={{ textAlign: "center", padding: "10px 0" }}>
        <div style={{
          fontFamily: "'Playfair Display', serif", fontStyle: "italic",
          color: "white", fontSize: 20, lineHeight: 1.4, marginBottom: 12,
        }}>{headline}</div>
        {caption && (
          <div style={{ color: "rgba(255,255,255,0.85)", fontSize: 12, lineHeight: 1.6, maxWidth: 220, margin: "0 auto" }}>
            {caption.split("\n\n")[0]}
          </div>
        )}
        <div style={{
          background: "white", borderRadius: 10, padding: "10px 16px",
          marginTop: 14, fontSize: 12, fontWeight: 700, color: F, textAlign: "center",
        }}>Book a free consultation 💚</div>
      </div>

      {/* Swipe up */}
      <div style={{ textAlign: "center", color: "rgba(255,255,255,0.7)", fontSize: 11 }}>
        <div style={{ fontSize: 18 }}>↑</div>
        Book a session
      </div>
    </div>
  );
}

// ── Facebook / LinkedIn Ad ─────────────────────────────────────────────────────
function FBCard({ gradient, headline, caption, isLinkedIn }: {
  gradient: string; headline: string; caption: string; isLinkedIn: boolean;
}) {
  return (
    <div style={{
      background: "white", borderRadius: 8,
      boxShadow: "0 2px 12px rgba(0,0,0,0.12)", overflow: "hidden",
      fontFamily: "-apple-system, sans-serif", maxWidth: 420,
    }}>
      {/* Header */}
      <div style={{ padding: "12px 14px", display: "flex", alignItems: "center", gap: 10 }}>
        <img src={LOGO} alt="FCC" style={{ height: 40, width: "auto", flexShrink: 0 }} />
        <div style={{ fontSize: 12, color: "#666" }}>{isLinkedIn ? "Promoted · 🌐" : "Sponsored · 🌐"}</div>
      </div>

      {/* Image area */}
      <div style={{
        width: "100%", aspectRatio: "1.91/1", background: gradient,
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 28, textAlign: "center",
      }}>
        <div>
          <div style={{
            fontFamily: "'Playfair Display', serif", fontStyle: "italic",
            color: "white", fontSize: "clamp(15px, 2.5vw, 21px)", lineHeight: 1.4,
          }}>{headline}</div>
          <div style={{ color: "rgba(255,255,255,0.8)", fontSize: 13, marginTop: 8 }}>
            Jill Dzadey · Couples Counsellor
          </div>
        </div>
      </div>

      {/* Copy */}
      <div style={{ padding: "12px 14px", fontSize: 14, lineHeight: 1.55, color: "#1c1e21" }}>
        {caption.split("\n\n")[0]}
      </div>

      {/* Link bar */}
      <div style={{
        margin: "0 14px 12px", background: "#f0f2f5", borderRadius: 8,
        padding: "10px 12px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div>
          <div style={{ fontSize: 11, color: "#666", textTransform: "uppercase" }}>
            freedomcouplecounselling.com
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "#1c1e21", marginTop: 2 }}>
            Book a Session — Freedom Couple Counselling
          </div>
          <div style={{ fontSize: 13, color: "#606770" }}>Melbourne & online.</div>
        </div>
        <button style={{
          background: "#e4e6eb", color: "#1c1e21", border: "none",
          padding: "7px 14px", borderRadius: 6, fontSize: 14,
          fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap", marginLeft: 10,
        }}>Learn More</button>
      </div>

      {/* Actions */}
      <div style={{
        padding: "4px 14px 12px", display: "flex", gap: 4,
        borderTop: "1px solid #e4e6eb", marginTop: 4,
      }}>
        {["👍 Like", "💬 Comment", "↗ Share"].map(a => (
          <div key={a} style={{ flex: 1, padding: 8, textAlign: "center", fontSize: 13, color: "#666", fontWeight: 600 }}>
            {a}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Twitter / TikTok ───────────────────────────────────────────────────────────
function TweetCard({ gradient, headline, caption, isTikTok }: {
  gradient: string; headline: string; caption: string; isTikTok: boolean;
}) {
  if (isTikTok) {
    return (
      <div style={{
        width: 270, height: 480, borderRadius: 16, overflow: "hidden",
        background: gradient, display: "flex", flexDirection: "column",
        justifyContent: "flex-end", padding: 20, position: "relative",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
      }}>
        <div style={{
          position: "absolute", top: 16, left: 0, right: 0,
          display: "flex", justifyContent: "space-between", padding: "0 16px",
        }}>
          <span style={{ color: "white", fontSize: 11, fontWeight: 700 }}>freedomcouplecounselling</span>
          <span style={{ color: "white", fontSize: 11 }}>🔴 LIVE</span>
        </div>
        <div>
          <div style={{
            fontFamily: "'Playfair Display', serif", fontStyle: "italic",
            color: "white", fontSize: 18, lineHeight: 1.4, marginBottom: 10,
          }}>{headline}</div>
          <div style={{ color: "rgba(255,255,255,0.8)", fontSize: 12, lineHeight: 1.6 }}>
            {caption.split("\n\n")[0]}
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 16 }}>
            {["❤️", "💬", "🔁", "📤"].map(e => (
              <span key={e} style={{ fontSize: 22 }}>{e}</span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: "white", borderRadius: 12,
      boxShadow: "0 2px 12px rgba(0,0,0,0.1)", overflow: "hidden", maxWidth: 420,
      fontFamily: "-apple-system, sans-serif",
    }}>
      <div style={{ padding: "16px 16px 12px", display: "flex", gap: 12 }}>
        <img src={LOGO} alt="FCC" style={{ height: 44, width: "auto", flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div style={{ color: "#666", fontSize: 14 }}>@freedomcouplecounselling</div>
          <div style={{ marginTop: 10, fontSize: 15, lineHeight: 1.55, color: "#0f1419" }}>
            {headline}{caption ? "\n\n" + caption.split("\n\n")[0] : ""}
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 20 }}>
            {["💬", "🔁", "❤️", "📊", "↗"].map(e => (
              <span key={e} style={{ fontSize: 18, color: "#666" }}>{e}</span>
            ))}
          </div>
          <div style={{ marginTop: 8, fontSize: 13, color: "#666" }}>9:41 AM · Melbourne</div>
        </div>
      </div>
    </div>
  );
}

// ── Email ──────────────────────────────────────────────────────────────────────
function EmailCard({ gradient, headline, caption }: {
  gradient: string; headline: string; caption: string;
}) {
  return (
    <div style={{
      background: "white", borderRadius: 8,
      boxShadow: "0 2px 12px rgba(0,0,0,0.1)", overflow: "hidden",
      maxWidth: 480, fontFamily: "'Lato', sans-serif",
    }}>
      {/* Email chrome */}
      <div style={{ background: "#f8f8f8", borderBottom: "1px solid #e0e0e0", padding: "8px 14px", fontSize: 12, color: "#666" }}>
        <div><strong>From:</strong> Jill Dzadey &lt;hello@freedomcouplecounselling.com&gt;</div>
        <div style={{ marginTop: 2 }}><strong>Subject:</strong> {headline.replace(/^"/, "").replace(/"$/, "")}</div>
      </div>

      {/* Header */}
      <div style={{
        background: gradient, padding: "32px 28px", textAlign: "center",
      }}>
        <div style={{
          fontFamily: "'Playfair Display', serif", fontStyle: "italic",
          color: "white", fontSize: 22, lineHeight: 1.4, marginBottom: 10,
        }}>{headline}</div>
        <div style={{ color: "rgba(255,255,255,0.75)", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Freedom Couple Counselling · Melbourne
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: "24px 28px", fontSize: 15, lineHeight: 1.7, color: "#333" }}>
        {caption.split("\n\n").map((para, i) => (
          <p key={i} style={{ marginBottom: 16 }}>{para}</p>
        ))}
      </div>

      {/* CTA */}
      <div style={{ textAlign: "center", padding: "0 28px 28px" }}>
        <div style={{
          display: "inline-block", background: T, color: "white",
          borderRadius: 8, padding: "12px 28px", fontSize: 15, fontWeight: 700,
        }}>Book a Free Consultation</div>
      </div>

      <div style={{ background: "#f8f8f8", padding: "12px 28px", fontSize: 11, color: "#999", textAlign: "center", borderTop: "1px solid #e0e0e0" }}>
        Freedom Couple Counselling · Melbourne · Unsubscribe
      </div>
    </div>
  );
}
