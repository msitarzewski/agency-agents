// ---------------------------------------------------------------------------
// Skill: Token Risk Assessment
// Pulls on-chain data from multiple sources, scores the token, and returns
// a structured risk report with explicit red flags.
// ---------------------------------------------------------------------------

import {
  PermissionTier,
  type Skill,
  type SkillOutput,
  type ToolInvoker,
} from "../types/index.js";

export interface RiskReport {
  token: string;
  score: number;
  verdict: "safe" | "moderate" | "elevated" | "dangerous" | "avoid";
  flags: string[];
  details: {
    mintAuthority: string | null;
    freezeAuthority: string | null;
    supply: number;
    topHolderConcentration: number;
    liquidityUsd: number;
    lpLocked: boolean;
    volume24h: number;
    volumeLiquidityRatio: number;
    pairAge: string | null;
  };
}

export const riskAssessSkill: Skill = {
  name: "risk-assess",
  description: "Comprehensive token risk assessment with on-chain data from multiple sources",
  requiredTools: ["helius-token-metadata", "dexscreener-token", "birdeye-token-overview"],
  dependsOn: [],
  requiredPermission: PermissionTier.ReadOnly,

  async execute(params: Record<string, unknown>, invoke: ToolInvoker): Promise<SkillOutput> {
    const start = Date.now();
    const mint = params.mint as string ?? params.outputMint as string;

    if (!mint) {
      return {
        skillName: "risk-assess",
        success: false,
        data: null,
        error: "Missing required param: mint",
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    // Pull data from all sources in parallel
    const [metadataResult, dexResult, birdeyeResult] = await Promise.all([
      invoke({ toolName: "helius-token-metadata", params: { mint } }),
      invoke({ toolName: "dexscreener-token", params: { mint } }),
      invoke({ toolName: "birdeye-token-overview", params: { mint } }),
    ]);

    const flags: string[] = [];
    let score = 0;

    // --- Analyze on-chain metadata ---
    const metadata = metadataResult.data as Record<string, unknown> | null;
    const mintAuthority = metadata?.mintAuthority as string | null ?? null;
    const freezeAuthority = metadata?.freezeAuthority as string | null ?? null;
    const supply = Number(metadata?.supply ?? 0);

    if (mintAuthority) {
      flags.push("MINT_AUTHORITY_ACTIVE — deployer can mint unlimited tokens");
      score += 35;
    }
    if (freezeAuthority) {
      flags.push("FREEZE_AUTHORITY_ACTIVE — deployer can freeze any wallet");
      score += 25;
    }

    // --- Analyze holder distribution ---
    const topHolderConcentration = Number(metadata?.topHolderConcentration ?? 0);
    if (topHolderConcentration > 50) {
      flags.push(`TOP_10_HOLD_${topHolderConcentration.toFixed(1)}% — extreme concentration`);
      score += 20;
    } else if (topHolderConcentration > 30) {
      flags.push(`TOP_10_HOLD_${topHolderConcentration.toFixed(1)}% — moderate concentration`);
      score += 10;
    }

    // --- Analyze liquidity ---
    const dex = dexResult.data as Record<string, unknown> | null;
    const liquidityUsd = Number(dex?.liquidityUsd ?? 0);
    const lpLocked = Boolean(dex?.lpLocked);
    const volume24h = Number(dex?.volume24h ?? 0);
    const pairAge = dex?.pairAge as string | null ?? null;

    if (liquidityUsd < 10_000) {
      flags.push(`LIQUIDITY_$${liquidityUsd.toLocaleString()} — critically low`);
      score += 20;
    } else if (liquidityUsd < 50_000) {
      flags.push(`LIQUIDITY_$${liquidityUsd.toLocaleString()} — thin`);
      score += 10;
    }

    if (!lpLocked && liquidityUsd > 0) {
      flags.push("LP_NOT_LOCKED — liquidity can be pulled at any time");
      score += 15;
    }

    // --- Detect wash trading ---
    const volumeLiquidityRatio = liquidityUsd > 0 ? volume24h / liquidityUsd : 0;
    if (volumeLiquidityRatio > 10) {
      flags.push(`VOLUME/LIQUIDITY_RATIO_${volumeLiquidityRatio.toFixed(1)} — likely wash trading`);
      score += 15;
    }

    score = Math.min(score, 100);
    const verdict: RiskReport["verdict"] =
      score <= 15 ? "safe" :
      score <= 35 ? "moderate" :
      score <= 55 ? "elevated" :
      score <= 75 ? "dangerous" : "avoid";

    const report: RiskReport = {
      token: mint,
      score,
      verdict,
      flags,
      details: {
        mintAuthority,
        freezeAuthority,
        supply,
        topHolderConcentration,
        liquidityUsd,
        lpLocked,
        volume24h,
        volumeLiquidityRatio,
        pairAge,
      },
    };

    return {
      skillName: "risk-assess",
      success: true,
      data: report,
      toolCalls: [],
      durationMs: Date.now() - start,
    };
  },
};
