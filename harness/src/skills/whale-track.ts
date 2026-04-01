// ---------------------------------------------------------------------------
// Skill: Whale Wallet Tracker
// Monitors large transactions on a token using Helius webhooks/enhanced
// transactions API. Detects accumulation, distribution, and LP changes.
// ---------------------------------------------------------------------------

import {
  PermissionTier,
  type Skill,
  type SkillOutput,
  type ToolInvoker,
} from "../types/index.js";

export interface WhaleMovement {
  wallet: string;
  type: "buy" | "sell" | "transfer_in" | "transfer_out" | "lp_add" | "lp_remove";
  amount: number;
  valueUsd: number;
  timestamp: number;
  signature: string;
}

export interface WhaleReport {
  token: string;
  period: string;
  movements: WhaleMovement[];
  netFlow: number;
  largestBuy: WhaleMovement | null;
  largestSell: WhaleMovement | null;
  uniqueWhales: number;
  sentiment: "accumulating" | "distributing" | "neutral";
}

export const whaleTrackSkill: Skill = {
  name: "whale-track",
  description: "Track large wallet movements on a specific token to detect accumulation/distribution patterns",
  requiredTools: ["helius-enhanced-transactions", "birdeye-token-overview"],
  dependsOn: [],
  requiredPermission: PermissionTier.ReadOnly,

  async execute(params: Record<string, unknown>, invoke: ToolInvoker): Promise<SkillOutput> {
    const start = Date.now();
    const mint = params.mint as string;
    const minValueUsd = (params.minValueUsd as number) ?? 10_000;
    const period = (params.period as string) ?? "24h";

    if (!mint) {
      return {
        skillName: "whale-track",
        success: false,
        data: null,
        error: "Missing required param: mint",
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    // 1. Fetch recent large transactions
    const txResult = await invoke({
      toolName: "helius-enhanced-transactions",
      params: { mint, limit: 100 },
    });

    if (!txResult.success) {
      return {
        skillName: "whale-track",
        success: false,
        data: null,
        error: `Failed to fetch transactions: ${txResult.error}`,
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    // 2. Get current price for USD valuation
    const priceResult = await invoke({
      toolName: "birdeye-token-overview",
      params: { mint },
    });
    const currentPrice = Number((priceResult.data as Record<string, unknown>)?.price ?? 0);

    // 3. Parse and filter whale movements
    const rawTxs = txResult.data as Array<Record<string, unknown>>;
    const movements: WhaleMovement[] = [];

    for (const tx of rawTxs) {
      const amount = Number(tx.amount ?? 0);
      const valueUsd = amount * currentPrice;

      if (valueUsd < minValueUsd) continue;

      movements.push({
        wallet: tx.wallet as string,
        type: tx.type as WhaleMovement["type"],
        amount,
        valueUsd,
        timestamp: tx.timestamp as number,
        signature: tx.signature as string,
      });
    }

    // 4. Calculate net flow and sentiment
    let buyVolume = 0;
    let sellVolume = 0;

    for (const m of movements) {
      if (m.type === "buy" || m.type === "transfer_in" || m.type === "lp_add") {
        buyVolume += m.valueUsd;
      } else {
        sellVolume += m.valueUsd;
      }
    }

    const netFlow = buyVolume - sellVolume;
    const sentiment: WhaleReport["sentiment"] =
      netFlow > buyVolume * 0.2 ? "accumulating" :
      netFlow < -sellVolume * 0.2 ? "distributing" : "neutral";

    const uniqueWhales = new Set(movements.map((m) => m.wallet)).size;

    const buys = movements.filter((m) => m.type === "buy");
    const sells = movements.filter((m) => m.type === "sell");

    const report: WhaleReport = {
      token: mint,
      period,
      movements,
      netFlow,
      largestBuy: buys.sort((a, b) => b.valueUsd - a.valueUsd)[0] ?? null,
      largestSell: sells.sort((a, b) => b.valueUsd - a.valueUsd)[0] ?? null,
      uniqueWhales,
      sentiment,
    };

    return {
      skillName: "whale-track",
      success: true,
      data: report,
      toolCalls: [],
      durationMs: Date.now() - start,
    };
  },
};
