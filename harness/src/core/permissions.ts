// ---------------------------------------------------------------------------
// Pattern 5: Permission System
// Tiered permissions that gate tool execution. Implemented as a pre-hook
// so it composes naturally with the hook pipeline.
// ---------------------------------------------------------------------------

import {
  HookPhase,
  HookVerdict,
  PermissionTier,
  type Hook,
  type HookContext,
  type HookResult,
  type ToolDefinition,
} from "../types/index.js";

/** Numeric ordering of tiers for comparison. */
const TIER_LEVEL: Record<PermissionTier, number> = {
  [PermissionTier.ReadOnly]: 0,
  [PermissionTier.Standard]: 1,
  [PermissionTier.Elevated]: 2,
  [PermissionTier.Full]: 3,
};

export class PermissionSystem {
  private toolPermissions = new Map<string, PermissionTier>();
  private denialLog: Array<{
    timestamp: number;
    sessionId: string;
    tool: string;
    requiredTier: PermissionTier;
    actualTier: PermissionTier;
  }> = [];

  /** Register the permission tier required for a tool. */
  setToolPermission(toolName: string, tier: PermissionTier): void {
    this.toolPermissions.set(toolName, tier);
  }

  /** Bulk-register from tool definitions. */
  registerTools(tools: ToolDefinition[]): void {
    for (const tool of tools) {
      this.toolPermissions.set(tool.name, tool.requiredPermission);
    }
  }

  /** Check if a given tier can invoke a tool. */
  canInvoke(toolName: string, tier: PermissionTier): boolean {
    const required = this.toolPermissions.get(toolName);
    if (!required) return true; // Unknown tools default to allowed (hook chain handles unknowns)
    return TIER_LEVEL[tier] >= TIER_LEVEL[required];
  }

  /**
   * Create a pre-hook that enforces permissions. This hook runs at high
   * priority (10) so it gates before business logic hooks.
   */
  toHook(): Hook {
    return {
      name: "permission-gate",
      phase: HookPhase.PreToolUse,
      priority: 10,
      execute: async (ctx: HookContext): Promise<HookResult> => {
        const required = this.toolPermissions.get(ctx.toolInput.toolName);

        // No permission registered = allow (other hooks can still deny)
        if (!required) {
          return { verdict: HookVerdict.Allow };
        }

        if (TIER_LEVEL[ctx.permissionTier] >= TIER_LEVEL[required]) {
          return { verdict: HookVerdict.Allow };
        }

        // Log the denial
        this.denialLog.push({
          timestamp: Date.now(),
          sessionId: ctx.sessionId,
          tool: ctx.toolInput.toolName,
          requiredTier: required,
          actualTier: ctx.permissionTier,
        });

        return {
          verdict: HookVerdict.Deny,
          reason: `Permission denied: "${ctx.toolInput.toolName}" requires ${required}, session has ${ctx.permissionTier}`,
        };
      },
    };
  }

  /** Get recent denials for monitoring/alerting. */
  getRecentDenials(since?: number): typeof this.denialLog {
    if (!since) return [...this.denialLog];
    return this.denialLog.filter((d) => d.timestamp >= since);
  }

  /** Check if an agent is repeatedly hitting permission walls. */
  isDenialSpike(sessionId: string, windowMs: number = 60_000, threshold: number = 5): boolean {
    const cutoff = Date.now() - windowMs;
    const recent = this.denialLog.filter(
      (d) => d.sessionId === sessionId && d.timestamp >= cutoff,
    );
    return recent.length >= threshold;
  }
}
