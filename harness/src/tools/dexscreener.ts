// ---------------------------------------------------------------------------
// Tool: DexScreener API
// Token pair data, liquidity info, LP lock status. Free tier, no key.
// ---------------------------------------------------------------------------

import { PermissionTier, type ToolDefinition } from "../types/index.js";
import type { ToolHandler } from "../core/executor.js";

const DEXSCREENER_API = "https://api.dexscreener.com";

// -- Tool definitions -------------------------------------------------------

export const dexscreenerTokenDef: ToolDefinition = {
  name: "dexscreener-token",
  description: "Fetch token pair data including liquidity, volume, and LP lock status from DexScreener",
  requiredPermission: PermissionTier.ReadOnly,
  inputSchema: {
    type: "object",
    required: ["mint"],
    properties: {
      mint: { type: "string", description: "Token mint address" },
    },
  },
  outputSchema: {
    type: "object",
    properties: {
      liquidityUsd: { type: "number" },
      lpLocked: { type: "boolean" },
      volume24h: { type: "number" },
      priceUsd: { type: "number" },
      priceChange24h: { type: "number" },
      pairAge: { type: "string" },
      dexId: { type: "string" },
      pairAddress: { type: "string" },
    },
  },
};

// -- Tool handler -----------------------------------------------------------

export const dexscreenerTokenHandler: ToolHandler = async (params) => {
  const mint = params.mint as string;

  const res = await fetch(`${DEXSCREENER_API}/latest/dex/tokens/${mint}`);
  if (!res.ok) throw new Error(`DexScreener failed: ${res.status}`);
  const body = await res.json() as { pairs: Array<Record<string, unknown>> | null };

  const pairs = body.pairs ?? [];
  if (pairs.length === 0) {
    return {
      liquidityUsd: 0,
      lpLocked: false,
      volume24h: 0,
      priceUsd: 0,
      priceChange24h: 0,
      pairAge: null,
      dexId: null,
      pairAddress: null,
    };
  }

  // Use the highest-liquidity pair
  const sorted = [...pairs].sort(
    (a, b) => Number((b as any).liquidity?.usd ?? 0) - Number((a as any).liquidity?.usd ?? 0),
  );
  const top = sorted[0] as any;

  return {
    liquidityUsd: top.liquidity?.usd ?? 0,
    lpLocked: Boolean(top.liquidity?.locked),
    volume24h: top.volume?.h24 ?? 0,
    priceUsd: Number(top.priceUsd ?? 0),
    priceChange24h: top.priceChange?.h24 ?? 0,
    pairAge: top.pairCreatedAt ? new Date(top.pairCreatedAt).toISOString() : null,
    dexId: top.dexId ?? null,
    pairAddress: top.pairAddress ?? null,
  };
};

export const dexscreenerTools = {
  definitions: [dexscreenerTokenDef],
  handlers: {
    "dexscreener-token": dexscreenerTokenHandler,
  } as Record<string, ToolHandler>,
};
