// ---------------------------------------------------------------------------
// Tool: Birdeye API
// Token overview, price data, volume analysis.
// ---------------------------------------------------------------------------

import { PermissionTier, type ToolDefinition } from "../types/index.js";
import type { ToolHandler } from "../core/executor.js";

const BIRDEYE_API = "https://public-api.birdeye.so";

// -- Tool definitions -------------------------------------------------------

export const birdeyeTokenOverviewDef: ToolDefinition = {
  name: "birdeye-token-overview",
  description: "Fetch token overview including price, volume, liquidity, and market cap from Birdeye",
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
      price: { type: "number" },
      priceChange24h: { type: "number" },
      volume24h: { type: "number" },
      liquidity: { type: "number" },
      marketCap: { type: "number" },
      supply: { type: "number" },
      holder: { type: "number" },
    },
  },
};

// -- Tool handlers ----------------------------------------------------------

export function createBirdeyeHandlers(apiKey: string) {
  const tokenOverviewHandler: ToolHandler = async (params) => {
    const mint = params.mint as string;

    const res = await fetch(`${BIRDEYE_API}/defi/token_overview?address=${mint}`, {
      headers: {
        "X-API-KEY": apiKey,
        "x-chain": "solana",
      },
    });
    if (!res.ok) throw new Error(`Birdeye overview failed: ${res.status}`);
    const body = await res.json() as { data: Record<string, unknown> };

    return {
      price: body.data?.price,
      priceChange24h: body.data?.priceChange24hPercent,
      volume24h: body.data?.v24hUSD,
      liquidity: body.data?.liquidity,
      marketCap: body.data?.mc,
      supply: body.data?.supply,
      holder: body.data?.holder,
    };
  };

  return {
    "birdeye-token-overview": tokenOverviewHandler,
  } as Record<string, ToolHandler>;
}

export const birdeyeTools = {
  definitions: [birdeyeTokenOverviewDef],
  createHandlers: createBirdeyeHandlers,
};
