// Model price table, spend ledger and monthly budget guard.
import { readCollection, insert } from "./store.js";
import { getSettings } from "./config.js";
import { emit } from "./events.js";

// USD per 1M tokens (Anthropic first-party prices, 2026-10).
// cacheRead for Haiku 5.5 is estimated at 0.1x input; cache writes bill at 1.25x input.
export const TIERS = {
  local: { label: "Local (Ollama) - miễn phí", provider: "ollama", in: 0, out: 0, cacheRead: 0 },
  eco: { label: "Tiết kiệm - Claude Haiku 5.5", provider: "anthropic", model: "claude-haiku-5-5", in: 0.1, out: 0.5, cacheRead: 0.01, effort: "low" },
  balanced: { label: "Cân bằng - Claude Sonnet 5.5", provider: "anthropic", model: "claude-sonnet-5-5", in: 2, out: 10, cacheRead: 0.2, effort: "medium" },
  premium: { label: "Cao cấp - Claude Opus 5.5", provider: "anthropic", model: "claude-opus-5-5", in: 4, out: 20, cacheRead: 0.2, effort: "high" },
};

export function tierForModel(model) {
  return Object.values(TIERS).find((t) => t.model === model);
}

export function costOf(tier, usage = {}) {
  const t = TIERS[tier];
  if (!t) return 0;
  const input = usage.input_tokens || 0;
  const cacheWrite = usage.cache_creation_input_tokens || 0;
  const cacheRead = usage.cache_read_input_tokens || 0;
  const output = usage.output_tokens || 0;
  return (input * t.in + cacheWrite * t.in * 1.25 + cacheRead * t.cacheRead + output * t.out) / 1e6;
}

// Rough pre-flight estimate (about 3.5 chars per token) used by the budget guard.
export function estimateCost(tier, inputChars, maxOutputTokens) {
  const t = TIERS[tier];
  if (!t) return 0;
  const inTok = Math.ceil(inputChars / 3.5);
  const outTok = Math.min(maxOutputTokens, 4000); // typical, not worst case
  return (inTok * t.in + outTok * t.out) / 1e6;
}

function monthKey(d = new Date()) {
  return d.toISOString().slice(0, 7);
}

export function record(entry) {
  const before = monthSpend();
  const row = insert("ledger", { ...entry, at: new Date().toISOString() });
  const { monthlyBudgetUsd } = getSettings();
  const after = before + (entry.costUsd || 0);
  if (monthlyBudgetUsd && before < 0.8 * monthlyBudgetUsd && after >= 0.8 * monthlyBudgetUsd) {
    emit("budget.warning", { spentUsd: after, budgetUsd: monthlyBudgetUsd, percent: Math.round((after / monthlyBudgetUsd) * 100) });
  }
  return row;
}

export function monthSpend(month = monthKey()) {
  return readCollection("ledger")
    .filter((e) => (e.at || "").startsWith(month))
    .reduce((s, e) => s + (e.costUsd || 0), 0);
}

export class BudgetError extends Error {}

export function assertBudget(estimateUsd) {
  const { monthlyBudgetUsd } = getSettings();
  if (!monthlyBudgetUsd) return;
  const spent = monthSpend();
  if (spent + estimateUsd > monthlyBudgetUsd) {
    emit("budget.exceeded", { spentUsd: spent, budgetUsd: monthlyBudgetUsd, requestEstimateUsd: estimateUsd });
    throw new BudgetError(
      `Vượt ngân sách tháng: đã dùng $${spent.toFixed(3)} / $${monthlyBudgetUsd}. ` +
        `Tác vụ này ước tính $${estimateUsd.toFixed(3)}. Tăng ngân sách trong Cài đặt hoặc chọn mức rẻ hơn.`
    );
  }
}

export function report() {
  const ledger = readCollection("ledger");
  const month = monthKey();
  const rows = ledger.filter((e) => (e.at || "").startsWith(month));
  const sum = (key) =>
    rows.reduce((acc, e) => {
      const k = e[key] || "khác";
      acc[k] = (acc[k] || 0) + (e.costUsd || 0);
      return acc;
    }, {});
  const saved = rows.reduce((s, e) => s + (e.savedUsd || 0), 0);
  return {
    month,
    budgetUsd: getSettings().monthlyBudgetUsd,
    spentUsd: rows.reduce((s, e) => s + (e.costUsd || 0), 0),
    savedUsd: saved,
    calls: rows.length,
    byTier: sum("tier"),
    byTask: sum("task"),
    recent: ledger.slice(-30).reverse(),
  };
}
