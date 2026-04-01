// ---------------------------------------------------------------------------
// Tool: Helius RPC & DAS API
// Token metadata, holder analysis, enhanced transaction history.
// ---------------------------------------------------------------------------

import { PermissionTier, type ToolDefinition } from "../types/index.js";
import type { ToolHandler } from "../core/executor.js";

// -- Tool definitions -------------------------------------------------------

export const heliusTokenMetadataDef: ToolDefinition = {
  name: "helius-token-metadata",
  description: "Fetch token metadata including mint/freeze authority, supply, and holder distribution via Helius DAS",
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
      mintAuthority: { type: "string", nullable: true },
      freezeAuthority: { type: "string", nullable: true },
      supply: { type: "number" },
      decimals: { type: "number" },
      topHolderConcentration: { type: "number" },
      topHolders: { type: "array" },
    },
  },
};

export const heliusEnhancedTransactionsDef: ToolDefinition = {
  name: "helius-enhanced-transactions",
  description: "Fetch parsed, enriched transaction history for a token via Helius Enhanced Transactions API",
  requiredPermission: PermissionTier.ReadOnly,
  inputSchema: {
    type: "object",
    required: ["mint"],
    properties: {
      mint: { type: "string" },
      limit: { type: "number", default: 50 },
    },
  },
  outputSchema: {
    type: "array",
    items: {
      type: "object",
      properties: {
        signature: { type: "string" },
        timestamp: { type: "number" },
        type: { type: "string" },
        wallet: { type: "string" },
        amount: { type: "number" },
      },
    },
  },
};

// -- Tool handlers ----------------------------------------------------------

function heliusUrl(apiKey: string, path: string): string {
  return `https://api.helius.xyz${path}?api-key=${apiKey}`;
}

export function createHeliusHandlers(apiKey: string) {
  const tokenMetadataHandler: ToolHandler = async (params) => {
    const mint = params.mint as string;

    // Fetch asset metadata via DAS
    const assetRes = await fetch(heliusUrl(apiKey, "/v0/token-metadata"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mintAccounts: [mint], includeOffChain: true }),
    });
    if (!assetRes.ok) throw new Error(`Helius metadata failed: ${assetRes.status}`);
    const assets = await assetRes.json() as Array<Record<string, unknown>>;
    const asset = assets[0];

    // Fetch top holders
    const holdersRes = await fetch(heliusUrl(apiKey, "/v0/token-accounts"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mint,
        limit: 20,
        sortBy: { sortBy: "amount", sortDirection: "desc" },
      }),
    });
    const holdersData = await holdersRes.json() as { token_accounts: Array<{ amount: string }> };
    const holders = holdersData.token_accounts ?? [];

    const totalSupply = Number((asset as any)?.onChainAccountInfo?.accountInfo?.data?.parsed?.info?.supply ?? 0);
    const topTenAmount = holders.slice(0, 10).reduce((s, h) => s + Number(h.amount), 0);
    const topHolderConcentration = totalSupply > 0 ? (topTenAmount / totalSupply) * 100 : 0;

    return {
      mintAuthority: (asset as any)?.onChainAccountInfo?.accountInfo?.data?.parsed?.info?.mintAuthority ?? null,
      freezeAuthority: (asset as any)?.onChainAccountInfo?.accountInfo?.data?.parsed?.info?.freezeAuthority ?? null,
      supply: totalSupply,
      decimals: (asset as any)?.onChainAccountInfo?.accountInfo?.data?.parsed?.info?.decimals ?? 0,
      topHolderConcentration,
      topHolders: holders.slice(0, 10),
    };
  };

  const enhancedTransactionsHandler: ToolHandler = async (params) => {
    const mint = params.mint as string;
    const limit = (params.limit as number) ?? 50;

    const res = await fetch(heliusUrl(apiKey, `/v0/addresses/${mint}/transactions`), {
      method: "GET",
    });
    if (!res.ok) throw new Error(`Helius transactions failed: ${res.status}`);
    const txs = await res.json() as Array<Record<string, unknown>>;

    return txs.slice(0, limit).map((tx) => ({
      signature: tx.signature,
      timestamp: tx.timestamp,
      type: tx.type,
      wallet: tx.feePayer,
      amount: (tx as any).tokenTransfers?.[0]?.tokenAmount ?? 0,
    }));
  };

  return {
    "helius-token-metadata": tokenMetadataHandler,
    "helius-enhanced-transactions": enhancedTransactionsHandler,
  } as Record<string, ToolHandler>;
}

export const heliusTools = {
  definitions: [heliusTokenMetadataDef, heliusEnhancedTransactionsDef],
  createHandlers: createHeliusHandlers,
};
