// ---------------------------------------------------------------------------
// Safety Hooks: Kuro-7 Solana Trading Guard Rails
// Pre-hooks that enforce risk management, rug protection, and tx simulation.
// All fail closed — if the hook errors, the action is denied.
// ---------------------------------------------------------------------------

import {
  HookPhase,
  HookVerdict,
  type Hook,
  type HookContext,
  type HookResult,
} from "../types/index.js";

// ---------------------------------------------------------------------------
// Hook: Rug Pull Protection
// Denies any swap into a token that fails basic safety checks.
// Runs at priority 20 (after permission gate at 10).
// ---------------------------------------------------------------------------

export function createRugProtectionHook(opts: {
  /** Minimum liquidity in USD to allow a trade. */
  minLiquidityUsd: number;
  /** Block trades into tokens with active mint authority. */
  blockMintAuthority: boolean;
}): Hook {
  return {
    name: "rug-protection",
    phase: HookPhase.PreToolUse,
    priority: 20,

    async execute(ctx: HookContext): Promise<HookResult> {
      // Only gate swap execution, not reads
      if (ctx.toolInput.toolName !== "jupiter-swap") {
        return { verdict: HookVerdict.Allow };
      }

      const riskReport = ctx.metadata.riskReport as Record<string, unknown> | undefined;
      if (!riskReport) {
        return {
          verdict: HookVerdict.Deny,
          reason: "Cannot execute swap without a prior risk assessment. Run risk-assess first.",
        };
      }

      // Block if mint authority is active
      if (opts.blockMintAuthority && riskReport.mintAuthority) {
        return {
          verdict: HookVerdict.Deny,
          reason: `Mint authority is active (${riskReport.mintAuthority}). Token supply can be inflated at any time. Trade blocked.`,
        };
      }

      // Block if liquidity is below threshold
      const liquidity = Number(riskReport.liquidityUsd ?? 0);
      if (liquidity < opts.minLiquidityUsd) {
        return {
          verdict: HookVerdict.Deny,
          reason: `Liquidity $${liquidity.toLocaleString()} is below minimum $${opts.minLiquidityUsd.toLocaleString()}. Trade blocked.`,
        };
      }

      // Block if risk score is "avoid"
      if (riskReport.verdict === "avoid") {
        return {
          verdict: HookVerdict.Deny,
          reason: `Risk verdict is "avoid" (score: ${riskReport.score}). Trade blocked.`,
        };
      }

      return { verdict: HookVerdict.Allow };
    },
  };
}

// ---------------------------------------------------------------------------
// Hook: Position Size Limit
// Ensures no single trade exceeds the configured portfolio percentage.
// ---------------------------------------------------------------------------

export function createPositionLimitHook(opts: {
  /** Maximum percentage of portfolio per trade (0-100). */
  maxPositionPct: number;
  /** Current portfolio value in USD (updated externally). */
  getPortfolioValueUsd: () => number;
}): Hook {
  return {
    name: "position-limit",
    phase: HookPhase.PreToolUse,
    priority: 25,

    async execute(ctx: HookContext): Promise<HookResult> {
      if (ctx.toolInput.toolName !== "jupiter-swap") {
        return { verdict: HookVerdict.Allow };
      }

      const tradeValueUsd = Number(ctx.toolInput.params.tradeValueUsd ?? 0);
      if (tradeValueUsd === 0) {
        return { verdict: HookVerdict.Allow };
      }

      const portfolioValue = opts.getPortfolioValueUsd();
      if (portfolioValue === 0) {
        return { verdict: HookVerdict.Allow };
      }

      const positionPct = (tradeValueUsd / portfolioValue) * 100;
      if (positionPct > opts.maxPositionPct) {
        return {
          verdict: HookVerdict.Deny,
          reason: `Trade is ${positionPct.toFixed(1)}% of portfolio (max: ${opts.maxPositionPct}%). Reduce position size.`,
        };
      }

      return { verdict: HookVerdict.Allow };
    },
  };
}

// ---------------------------------------------------------------------------
// Hook: Transaction Simulation Gate
// Ensures every swap transaction is simulated before submission.
// If simulation hasn't happened, denies the send.
// ---------------------------------------------------------------------------

export function createSimulationGateHook(): Hook {
  const simulatedTxs = new Set<string>();

  return {
    name: "simulation-gate",
    phase: HookPhase.PreToolUse,
    priority: 30,

    async execute(ctx: HookContext): Promise<HookResult> {
      // Track simulations
      if (ctx.toolInput.toolName === "solana-simulate-tx") {
        const txId = ctx.toolInput.params.transaction as string;
        if (txId) simulatedTxs.add(txId);
        return { verdict: HookVerdict.Allow };
      }

      // Gate raw transaction sends
      if (ctx.toolInput.toolName === "jupiter-swap") {
        const txId = ctx.toolInput.params.transactionId as string;
        if (txId && !simulatedTxs.has(txId)) {
          return {
            verdict: HookVerdict.Deny,
            reason: "Transaction must be simulated before submission. Call solana-simulate-tx first.",
          };
        }
      }

      return { verdict: HookVerdict.Allow };
    },
  };
}

// ---------------------------------------------------------------------------
// Hook: Rate Limiter
// Prevents rapid-fire tool calls that could indicate a runaway loop.
// ---------------------------------------------------------------------------

export function createRateLimitHook(opts: {
  /** Maximum tool calls per window. */
  maxCalls: number;
  /** Window size in ms. */
  windowMs: number;
}): Hook {
  const callTimestamps: number[] = [];

  return {
    name: "rate-limit",
    phase: HookPhase.PreToolUse,
    priority: 5,

    async execute(): Promise<HookResult> {
      const now = Date.now();
      const cutoff = now - opts.windowMs;

      // Prune old timestamps
      while (callTimestamps.length > 0 && callTimestamps[0] < cutoff) {
        callTimestamps.shift();
      }

      if (callTimestamps.length >= opts.maxCalls) {
        return {
          verdict: HookVerdict.Deny,
          reason: `Rate limit exceeded: ${opts.maxCalls} calls per ${opts.windowMs}ms window`,
        };
      }

      callTimestamps.push(now);
      return { verdict: HookVerdict.Allow };
    },
  };
}

// ---------------------------------------------------------------------------
// Hook: Audit Logger (Post-hook)
// Records every tool execution for the session audit trail.
// ---------------------------------------------------------------------------

export function createAuditLogHook(): Hook {
  return {
    name: "audit-log",
    phase: HookPhase.PostToolUse,
    priority: 0,

    async execute(ctx: HookContext): Promise<HookResult> {
      const entry = {
        timestamp: Date.now(),
        sessionId: ctx.sessionId,
        tool: ctx.toolInput.toolName,
        params: ctx.toolInput.params,
        success: ctx.toolOutput?.success,
        durationMs: ctx.toolOutput?.durationMs,
        error: ctx.toolOutput?.error,
      };

      // In production, pipe to observability (Datadog, CloudWatch, etc.)
      // For now, structured console log
      console.log(JSON.stringify({ type: "audit", ...entry }));

      return { verdict: HookVerdict.Allow };
    },
  };
}
