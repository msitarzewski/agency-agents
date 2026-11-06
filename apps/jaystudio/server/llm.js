// Cost-aware LLM router.
// Order of savings: response cache ($0) -> local Ollama ($0) -> prompt caching -> cheapest tier that
// holds quality for the task -> budget guard. Claude is called through the official Anthropic SDK.
import Anthropic from "@anthropic-ai/sdk";
import { getSettings } from "./config.js";
import { TIERS, costOf, estimateCost, assertBudget, record } from "./costs.js";
import { readMap, writeMap, hash } from "./store.js";

// Default tier per task: spend on thinking where it pays off, save on volume work.
export const TASK_TIER = {
  strategy: "premium", // brand positioning: done rarely, quality matters most
  budget: "premium", // marketing budget allocation
  calendar: "balanced",
  content: "balanced",
  videoSpec: "balanced",
  assistant: "balanced",
  repurpose: "eco", // rewriting existing content into other formats
  variants: "eco", // A/B headlines, hashtags, captions
};

let client = null;
function anthropic() {
  if (!client) client = new Anthropic(); // reads ANTHROPIC_API_KEY / ant auth profile
  return client;
}

export function anthropicConfigured() {
  return Boolean(process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_AUTH_TOKEN || process.env.ANTHROPIC_PROFILE);
}

let ollamaState = { at: 0, ok: false, models: [] };
export async function ollamaStatus() {
  const s = getSettings();
  if (Date.now() - ollamaState.at < 30_000) return ollamaState;
  try {
    const r = await fetch(`${s.ollamaUrl}/api/tags`, { signal: AbortSignal.timeout(1500) });
    const j = await r.json();
    ollamaState = { at: Date.now(), ok: r.ok, models: (j.models || []).map((m) => m.name) };
  } catch {
    ollamaState = { at: Date.now(), ok: false, models: [] };
  }
  return ollamaState;
}

export async function resolveTier(task, requested) {
  const s = getSettings();
  let tier = requested && requested !== "auto" ? requested : s.tierOverrides[task] || TASK_TIER[task] || "balanced";
  if (tier === "eco" && s.freeFirst) {
    const o = await ollamaStatus();
    if (o.ok && o.models.some((m) => m.startsWith(s.ollamaModel.split(":")[0]))) tier = "local";
  }
  if (tier === "local" && !(await ollamaStatus()).ok) tier = "eco";
  return tier;
}

function textOf(content) {
  return content
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("\n")
    .trim();
}

async function callOllama(systemText, prompt) {
  const s = getSettings();
  const r = await fetch(`${s.ollamaUrl}/api/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      model: s.ollamaModel,
      stream: false,
      messages: [
        { role: "system", content: systemText },
        { role: "user", content: prompt },
      ],
    }),
  });
  if (!r.ok) throw new Error(`Ollama lỗi ${r.status}`);
  const j = await r.json();
  return j.message?.content || "";
}

// Build a Messages API request for a tier. Opus/Sonnet get server-side refusal fallbacks.
function requestFor(tier, { system, messages, maxTokens, tools }) {
  const t = TIERS[tier];
  const req = {
    model: t.model,
    max_tokens: maxTokens,
    system,
    messages,
    output_config: { effort: t.effort },
  };
  if (tools?.length) req.tools = tools;
  if (tier === "premium" || tier === "balanced") {
    req.betas = ["server-side-fallback-2026-07-01"];
    req.fallbacks = "default";
  }
  return req;
}

async function send(tier, req) {
  const api = anthropic();
  // Streaming avoids HTTP timeouts on long outputs; finalMessage() returns the full response.
  const stream = req.betas ? api.beta.messages.stream(req) : api.messages.stream(req);
  return stream.finalMessage();
}

function explainError(err) {
  if (err instanceof Anthropic.AuthenticationError) return "Chưa có hoặc sai ANTHROPIC_API_KEY (đặt trong apps/jaystudio/.env).";
  if (err instanceof Anthropic.RateLimitError) return "Claude đang giới hạn tốc độ, thử lại sau ít phút.";
  if (err instanceof Anthropic.BadRequestError) return `Yêu cầu không hợp lệ: ${err.message}`;
  if (err instanceof Anthropic.APIError) return `Lỗi Claude API ${err.status}: ${err.message}`;
  return err.message || String(err);
}

/**
 * One-shot completion.
 * systemBlocks: [{ text, cache: true|false }] - stable blocks first so prompt caching hits.
 */
export async function complete({ task, tier: requested, systemBlocks, prompt, maxTokens = 16000, useCache = true }) {
  const s = getSettings();
  const tier = await resolveTier(task, requested);
  const systemText = systemBlocks.map((b) => b.text).join("\n\n");
  const cacheKey = hash(tier, systemText, prompt, maxTokens);

  if (useCache && s.responseCache) {
    const cache = readMap("response-cache");
    if (cache[cacheKey]) {
      const hit = cache[cacheKey];
      record({ task, tier, model: hit.model, costUsd: 0, savedUsd: hit.costUsd || 0, note: "cache" });
      return { ...hit, cached: true, costUsd: 0 };
    }
  }

  let result;
  if (tier === "local") {
    const text = await callOllama(systemText, prompt);
    const ref = estimateCost("eco", systemText.length + prompt.length, maxTokens);
    result = { text, model: `ollama:${s.ollamaModel}`, tier, costUsd: 0, usage: {} };
    record({ task, tier, model: result.model, costUsd: 0, savedUsd: ref });
  } else {
    if (!anthropicConfigured()) throw new Error("Chưa cấu hình ANTHROPIC_API_KEY trong apps/jaystudio/.env.");
    assertBudget(estimateCost(tier, systemText.length + prompt.length, maxTokens));
    const system = systemBlocks.map((b) => ({ type: "text", text: b.text }));
    // A cache breakpoint on the last stable block caches every block before it too.
    const lastCacheIdx = systemBlocks.map((b) => b.cache).lastIndexOf(true);
    if (lastCacheIdx >= 0) system[lastCacheIdx].cache_control = { type: "ephemeral" };

    let msg;
    try {
      msg = await send(tier, requestFor(tier, { system, messages: [{ role: "user", content: prompt }], maxTokens }));
    } catch (err) {
      throw new Error(explainError(err));
    }
    if (msg.stop_reason === "refusal") {
      throw new Error(`Claude từ chối yêu cầu này (${msg.stop_details?.category || "không rõ"}). Hãy diễn đạt lại.`);
    }
    const tierUsed = Object.keys(TIERS).find((k) => TIERS[k].model === msg.model) || tier;
    const costUsd = costOf(tierUsed, msg.usage);
    result = {
      text: textOf(msg.content),
      model: msg.model,
      tier: tierUsed,
      costUsd,
      usage: msg.usage,
      truncated: msg.stop_reason === "max_tokens",
    };
    record({ task, tier: tierUsed, model: msg.model, costUsd, usage: msg.usage });
  }

  if (s.responseCache && result.text) {
    const cache = readMap("response-cache");
    cache[cacheKey] = { text: result.text, model: result.model, tier: result.tier, costUsd: result.costUsd, at: new Date().toISOString() };
    writeMap("response-cache", cache);
  }
  return result;
}

/** One assistant turn with tools. Returns the raw message so callers can run the tool loop. */
export async function chatTurn({ tier: requested, system, messages, tools, maxTokens = 16000 }) {
  let tier = await resolveTier("assistant", requested);
  if (tier === "local") tier = "eco"; // tool use runs on Claude
  if (!anthropicConfigured()) throw new Error("Chưa cấu hình ANTHROPIC_API_KEY trong apps/jaystudio/.env.");
  assertBudget(estimateCost(tier, JSON.stringify(messages).length + JSON.stringify(tools).length, maxTokens));
  let msg;
  try {
    msg = await send(tier, requestFor(tier, { system, messages, maxTokens, tools }));
  } catch (err) {
    throw new Error(explainError(err));
  }
  const tierUsed = Object.keys(TIERS).find((k) => TIERS[k].model === msg.model) || tier;
  const costUsd = costOf(tierUsed, msg.usage);
  record({ task: "assistant", tier: tierUsed, model: msg.model, costUsd, usage: msg.usage });
  return { msg, costUsd, tier: tierUsed };
}
