// ---------------------------------------------------------------------------
// Pattern 2: Hook System (PreToolUse / PostToolUse)
// Unified interception pipeline. Pre-hooks validate, gate, rewrite.
// Post-hooks log, trigger follow-ups, update state.
// Pre-hook denial is fail-safe: errors = denied.
// ---------------------------------------------------------------------------

import {
  HookPhase,
  HookVerdict,
  type Hook,
  type HookContext,
  type HookResult,
  type ToolInput,
} from "../types/index.js";

export interface PreHookResult {
  denied: boolean;
  deniedBy?: string;
  reason?: string;
  rewrittenInput?: ToolInput;
}

export class HookPipeline {
  private hooks: Hook[] = [];

  /** Register a hook. Hooks are sorted by priority (lower = runs first). */
  register(hook: Hook): void {
    this.hooks.push(hook);
    this.hooks.sort((a, b) => a.priority - b.priority);
  }

  /** Remove a hook by name. */
  unregister(name: string): void {
    this.hooks = this.hooks.filter((h) => h.name !== name);
  }

  /**
   * Run all pre-hooks in priority order. If any hook denies, the chain stops
   * immediately. If any hook throws, the action is denied (fail-closed).
   * Rewrite verdicts mutate the context for subsequent hooks.
   */
  async runPreHooks(ctx: HookContext): Promise<PreHookResult> {
    const preHooks = this.hooks.filter((h) => h.phase === HookPhase.PreToolUse);
    let currentInput = ctx.toolInput;

    for (const hook of preHooks) {
      let result: HookResult;
      try {
        result = await hook.execute({ ...ctx, toolInput: currentInput });
      } catch (err) {
        // Fail closed: hook error = deny
        return {
          denied: true,
          deniedBy: hook.name,
          reason: `Hook threw error (fail-closed): ${String(err)}`,
        };
      }

      if (result.verdict === HookVerdict.Deny) {
        return {
          denied: true,
          deniedBy: hook.name,
          reason: result.reason ?? "Denied by hook",
        };
      }

      if (result.verdict === HookVerdict.Rewrite && result.rewrittenContext?.toolInput) {
        currentInput = result.rewrittenContext.toolInput;
      }
    }

    return {
      denied: false,
      rewrittenInput: currentInput,
    };
  }

  /**
   * Run all post-hooks in priority order. Post-hooks cannot deny — they
   * observe, log, and trigger side effects. Errors are swallowed with
   * a warning (post-hooks must not break the pipeline).
   */
  async runPostHooks(ctx: HookContext): Promise<void> {
    const postHooks = this.hooks.filter((h) => h.phase === HookPhase.PostToolUse);

    for (const hook of postHooks) {
      try {
        await hook.execute(ctx);
      } catch {
        // Post-hook errors are logged but do not break execution.
        // In production, pipe to observability.
        console.warn(`[hook:${hook.name}] Post-hook error (swallowed)`);
      }
    }
  }

  /** List all registered hooks (for debugging/introspection). */
  list(): Array<{ name: string; phase: HookPhase; priority: number }> {
    return this.hooks.map((h) => ({
      name: h.name,
      phase: h.phase,
      priority: h.priority,
    }));
  }
}
