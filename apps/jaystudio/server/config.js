// Paths, environment and user settings for Jaystudio Brand OS.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const APP_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const REPO_ROOT = path.resolve(APP_DIR, "..", "..");
export const DATA_DIR = process.env.JAYSTUDIO_DATA_DIR || path.join(APP_DIR, "data");
export const PUBLIC_DIR = path.join(APP_DIR, "public");

// Load apps/jaystudio/.env if present (Node 22 built-in, no dotenv needed).
const envFile = path.join(APP_DIR, ".env");
if (fs.existsSync(envFile) && typeof process.loadEnvFile === "function") {
  process.loadEnvFile(envFile);
}

export const HOST = process.env.JAYSTUDIO_HOST || "127.0.0.1";
export const PORT = Number(process.env.JAYSTUDIO_PORT || 4321);
// Optional bearer token so other AIOS services can call the API safely.
export const API_TOKEN = process.env.JAYSTUDIO_API_TOKEN || "";

fs.mkdirSync(DATA_DIR, { recursive: true });

const SETTINGS_FILE = path.join(DATA_DIR, "settings.json");

export const DEFAULT_SETTINGS = {
  monthlyBudgetUsd: 20, // hard cap for AI spend tracked by this app
  currency: "VND",
  language: "vi",
  // "auto" = route each task to the cheapest tier that holds quality (see llm.js TASK_TIER)
  tierOverrides: {},
  freeFirst: true, // use local Ollama for "eco" tasks when it is running
  ollamaUrl: process.env.OLLAMA_URL || "http://127.0.0.1:11434",
  ollamaModel: process.env.OLLAMA_MODEL || "qwen2.5:7b",
  responseCache: true, // identical request => reuse saved answer, $0
  approvePaidTools: true, // assistant must ask before calling MCP tools that spend money
  assistantServers: ["mcp-video", "video-toolkit"],
};

export function getSettings() {
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(fs.readFileSync(SETTINGS_FILE, "utf8")) };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function saveSettings(patch) {
  const allowed = Object.keys(DEFAULT_SETTINGS);
  const next = getSettings();
  for (const [k, v] of Object.entries(patch || {})) if (allowed.includes(k)) next[k] = v;
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(next, null, 2));
  return next;
}

// API keys the connected tools can use. Only presence is ever reported, never values.
export const KNOWN_KEYS = [
  { env: "ANTHROPIC_API_KEY", use: "Claude: chiến lược, nội dung, trợ lý, dịch, chỉnh màu (VibeFrame)" },
  { env: "ELEVENLABS_API_KEY", use: "Giọng đọc, nhân bản giọng, SFX, nhạc, phụ đề Scribe" },
  { env: "GOOGLE_API_KEY", use: "Gemini: ảnh miễn phí, phân tích video, chọn thumbnail" },
  { env: "OPENAI_API_KEY", use: "Whisper, GPT Image, giọng OpenAI (tùy chọn)" },
  { env: "FAL_KEY", use: "Video AI Seedance (VibeFrame)" },
  { env: "KLING_API_KEY", use: "Video AI Kling" },
  { env: "RUNWAY_API_SECRET", use: "Video AI Runway" },
  { env: "REPLICATE_API_TOKEN", use: "MusicGen" },
  { env: "MODAL_TOKEN_ID", use: "Video toolkit: LTX, FLUX trên GPU Modal" },
  { env: "RUNPOD_API_KEY", use: "Video toolkit: GPU RunPod" },
];
