// ---------------------------------------------------------------------------
// Tool: Solana RPC
// Direct on-chain queries — token accounts, balances, transaction simulation.
// ---------------------------------------------------------------------------

import { PermissionTier, type ToolDefinition } from "../types/index.js";
import type { ToolHandler } from "../core/executor.js";

// -- Tool definitions -------------------------------------------------------

export const solanaGetTokenAccountsDef: ToolDefinition = {
  name: "solana-get-token-accounts",
  description: "Fetch all SPL token accounts for a wallet with balances and metadata",
  requiredPermission: PermissionTier.ReadOnly,
  inputSchema: {
    type: "object",
    required: ["wallet"],
    properties: {
      wallet: { type: "string", description: "Wallet public key" },
    },
  },
  outputSchema: {
    type: "array",
    items: {
      type: "object",
      properties: {
        mint: { type: "string" },
        symbol: { type: "string" },
        balance: { type: "number" },
        decimals: { type: "number" },
      },
    },
  },
};

export const solanaSimulateTxDef: ToolDefinition = {
  name: "solana-simulate-tx",
  description: "Simulate a transaction before sending to check for errors",
  requiredPermission: PermissionTier.ReadOnly,
  inputSchema: {
    type: "object",
    required: ["transaction"],
    properties: {
      transaction: { type: "string", description: "Base64-encoded transaction" },
    },
  },
  outputSchema: {
    type: "object",
    properties: {
      success: { type: "boolean" },
      error: { type: "string", nullable: true },
      logs: { type: "array", items: { type: "string" } },
      unitsConsumed: { type: "number" },
    },
  },
};

// -- Tool handlers ----------------------------------------------------------

export function createSolanaHandlers(rpcUrl: string) {
  const getTokenAccountsHandler: ToolHandler = async (params) => {
    const wallet = params.wallet as string;

    const res = await fetch(rpcUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "getTokenAccountsByOwner",
        params: [
          wallet,
          { programId: "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA" },
          { encoding: "jsonParsed" },
        ],
      }),
    });
    if (!res.ok) throw new Error(`Solana RPC failed: ${res.status}`);
    const body = await res.json() as { result: { value: Array<Record<string, unknown>> } };

    const accounts = body.result?.value ?? [];
    return accounts
      .map((acc: any) => {
        const info = acc.account?.data?.parsed?.info;
        return {
          mint: info?.mint,
          symbol: "UNKNOWN", // Resolved by the skill via Jupiter price API
          balance: Number(info?.tokenAmount?.uiAmount ?? 0),
          decimals: info?.tokenAmount?.decimals ?? 0,
        };
      })
      .filter((a: { balance: number }) => a.balance > 0);
  };

  const simulateTxHandler: ToolHandler = async (params) => {
    const transaction = params.transaction as string;

    const res = await fetch(rpcUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "simulateTransaction",
        params: [transaction, { encoding: "base64" }],
      }),
    });
    if (!res.ok) throw new Error(`Solana simulation failed: ${res.status}`);
    const body = await res.json() as { result: { value: Record<string, unknown> } };
    const value = body.result?.value;

    return {
      success: !value?.err,
      error: value?.err ? JSON.stringify(value.err) : null,
      logs: value?.logs ?? [],
      unitsConsumed: value?.unitsConsumed ?? 0,
    };
  };

  return {
    "solana-get-token-accounts": getTokenAccountsHandler,
    "solana-simulate-tx": simulateTxHandler,
  } as Record<string, ToolHandler>;
}

export const solanaTools = {
  definitions: [solanaGetTokenAccountsDef, solanaSimulateTxDef],
  createHandlers: createSolanaHandlers,
};
