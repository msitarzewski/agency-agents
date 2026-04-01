// ---------------------------------------------------------------------------
// Skill: Wallet Portfolio Scanner
// Reads all SPL token balances, fetches prices, calculates portfolio
// value and allocation percentages.
// ---------------------------------------------------------------------------

import {
  PermissionTier,
  type Skill,
  type SkillOutput,
  type ToolInvoker,
} from "../types/index.js";

export interface PortfolioPosition {
  mint: string;
  symbol: string;
  balance: number;
  priceUsd: number;
  valueUsd: number;
  allocationPct: number;
}

export interface PortfolioReport {
  wallet: string;
  totalValueUsd: number;
  positions: PortfolioPosition[];
  solBalance: number;
  solPrice: number;
  timestamp: number;
}

export const portfolioScanSkill: Skill = {
  name: "portfolio-scan",
  description: "Scan a wallet for all SPL token holdings with current USD valuations",
  requiredTools: ["solana-get-token-accounts", "jupiter-price"],
  dependsOn: [],
  requiredPermission: PermissionTier.ReadOnly,

  async execute(params: Record<string, unknown>, invoke: ToolInvoker): Promise<SkillOutput> {
    const start = Date.now();
    const wallet = params.wallet as string;

    if (!wallet) {
      return {
        skillName: "portfolio-scan",
        success: false,
        data: null,
        error: "Missing required param: wallet",
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    // 1. Fetch all token accounts for the wallet
    const accountsResult = await invoke({
      toolName: "solana-get-token-accounts",
      params: { wallet },
    });

    if (!accountsResult.success) {
      return {
        skillName: "portfolio-scan",
        success: false,
        data: null,
        error: `Failed to fetch token accounts: ${accountsResult.error}`,
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    const accounts = accountsResult.data as Array<{
      mint: string;
      symbol: string;
      balance: number;
    }>;

    // 2. Batch price lookup
    const mints = accounts.map((a) => a.mint);
    const priceResult = await invoke({
      toolName: "jupiter-price",
      params: { mints },
    });

    const prices = (priceResult.data as Record<string, number>) ?? {};

    // 3. Build positions
    const positions: PortfolioPosition[] = accounts.map((a) => ({
      mint: a.mint,
      symbol: a.symbol,
      balance: a.balance,
      priceUsd: prices[a.mint] ?? 0,
      valueUsd: a.balance * (prices[a.mint] ?? 0),
      allocationPct: 0,
    }));

    const totalValueUsd = positions.reduce((sum, p) => sum + p.valueUsd, 0);

    for (const p of positions) {
      p.allocationPct = totalValueUsd > 0 ? (p.valueUsd / totalValueUsd) * 100 : 0;
    }

    positions.sort((a, b) => b.valueUsd - a.valueUsd);

    // Extract SOL position
    const SOL_MINT = "So11111111111111111111111111111111111111112";
    const solPos = positions.find((p) => p.mint === SOL_MINT);

    const report: PortfolioReport = {
      wallet,
      totalValueUsd,
      positions,
      solBalance: solPos?.balance ?? 0,
      solPrice: solPos?.priceUsd ?? 0,
      timestamp: Date.now(),
    };

    return {
      skillName: "portfolio-scan",
      success: true,
      data: report,
      toolCalls: [],
      durationMs: Date.now() - start,
    };
  },
};
