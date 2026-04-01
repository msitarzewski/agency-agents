// ---------------------------------------------------------------------------
// Tool: Jupiter V6 API
// Quote, swap, price, DCA, and limit order endpoints.
// ---------------------------------------------------------------------------

import { PermissionTier, type ToolDefinition } from "../types/index.js";
import type { ToolHandler } from "../core/executor.js";

const JUPITER_API = "https://quote-api.jup.ag/v6";
const JUPITER_PRICE_API = "https://api.jup.ag/price/v2";

// -- Tool definitions -------------------------------------------------------

export const jupiterQuoteDef: ToolDefinition = {
  name: "jupiter-quote",
  description: "Get a swap quote from Jupiter V6 aggregator",
  requiredPermission: PermissionTier.ReadOnly,
  inputSchema: {
    type: "object",
    required: ["inputMint", "outputMint", "amount"],
    properties: {
      inputMint: { type: "string" },
      outputMint: { type: "string" },
      amount: { type: "number", description: "Amount in smallest unit (lamports)" },
      slippageBps: { type: "number", default: 50 },
    },
  },
  outputSchema: {
    type: "object",
    properties: {
      inputMint: { type: "string" },
      outputMint: { type: "string" },
      inAmount: { type: "string" },
      outAmount: { type: "string" },
      priceImpactPct: { type: "string" },
      routePlan: { type: "array" },
    },
  },
};

export const jupiterSwapDef: ToolDefinition = {
  name: "jupiter-swap",
  description: "Build and execute a swap transaction via Jupiter V6",
  requiredPermission: PermissionTier.Standard,
  inputSchema: {
    type: "object",
    required: ["quoteResponse"],
    properties: {
      quoteResponse: { type: "object" },
      userPublicKey: { type: "string" },
      wrapAndUnwrapSol: { type: "boolean", default: true },
      dynamicComputeUnitLimit: { type: "boolean", default: true },
      prioritizationFeeLamports: { type: "string", default: "auto" },
    },
  },
  outputSchema: {
    type: "object",
    properties: {
      signature: { type: "string" },
      confirmed: { type: "boolean" },
    },
  },
};

export const jupiterPriceDef: ToolDefinition = {
  name: "jupiter-price",
  description: "Batch price lookup for SPL tokens via Jupiter Price API",
  requiredPermission: PermissionTier.ReadOnly,
  inputSchema: {
    type: "object",
    required: ["mints"],
    properties: {
      mints: { type: "array", items: { type: "string" } },
    },
  },
  outputSchema: {
    type: "object",
    description: "Map of mint address to USD price",
  },
};

// -- Tool handlers ----------------------------------------------------------

export const jupiterQuoteHandler: ToolHandler = async (params) => {
  const url = new URL(`${JUPITER_API}/quote`);
  url.searchParams.set("inputMint", params.inputMint as string);
  url.searchParams.set("outputMint", params.outputMint as string);
  url.searchParams.set("amount", String(params.amount));
  url.searchParams.set("slippageBps", String(params.slippageBps ?? 50));

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Jupiter quote failed: ${res.status} ${await res.text()}`);
  return res.json();
};

export const jupiterSwapHandler: ToolHandler = async (params) => {
  const res = await fetch(`${JUPITER_API}/swap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      quoteResponse: params.quoteResponse,
      userPublicKey: params.userPublicKey,
      wrapAndUnwrapSol: params.wrapAndUnwrapSol ?? true,
      dynamicComputeUnitLimit: params.dynamicComputeUnitLimit ?? true,
      prioritizationFeeLamports: params.prioritizationFeeLamports ?? "auto",
    }),
  });
  if (!res.ok) throw new Error(`Jupiter swap failed: ${res.status} ${await res.text()}`);
  return res.json();
};

export const jupiterPriceHandler: ToolHandler = async (params) => {
  const mints = params.mints as string[];
  const ids = mints.join(",");
  const res = await fetch(`${JUPITER_PRICE_API}?ids=${ids}`);
  if (!res.ok) throw new Error(`Jupiter price failed: ${res.status}`);
  const data = await res.json() as { data: Record<string, { price: string }> };

  // Flatten to mint → price map
  const prices: Record<string, number> = {};
  for (const [mint, info] of Object.entries(data.data ?? {})) {
    prices[mint] = Number(info.price);
  }
  return prices;
};

export const jupiterTools = {
  definitions: [jupiterQuoteDef, jupiterSwapDef, jupiterPriceDef],
  handlers: {
    "jupiter-quote": jupiterQuoteHandler,
    "jupiter-swap": jupiterSwapHandler,
    "jupiter-price": jupiterPriceHandler,
  } as Record<string, ToolHandler>,
};
