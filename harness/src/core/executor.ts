// ---------------------------------------------------------------------------
// Pattern 1b: Execution Layer
// Invokes tools through the hook pipeline with retries and error handling.
// Completely decoupled from orchestration — swappable backend.
// ---------------------------------------------------------------------------

import type {
  Session,
  SkillInput,
  SkillOutput,
  ToolInput,
  ToolOutput,
} from "../types/index.js";
import { SessionEventType } from "../types/index.js";
import type { HookPipeline } from "./hooks.js";
import type { SkillRegistry } from "./registry.js";
import type { SessionManager } from "./session.js";

interface ExecutorConfig {
  /** Maximum retries per tool invocation. */
  maxRetries: number;
  /** Base delay between retries in ms (exponential backoff). */
  retryBaseMs: number;
  /** Maximum time for a single tool invocation in ms. */
  toolTimeoutMs: number;
}

const DEFAULT_CONFIG: ExecutorConfig = {
  maxRetries: 3,
  retryBaseMs: 500,
  toolTimeoutMs: 30_000,
};

export class Executor {
  private tools = new Map<string, ToolHandler>();
  private config: ExecutorConfig;

  constructor(
    private hooks: HookPipeline,
    private registry: SkillRegistry,
    private sessions: SessionManager,
    config?: Partial<ExecutorConfig>,
  ) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** Register a tool handler that the executor can invoke. */
  registerTool(name: string, handler: ToolHandler): void {
    this.tools.set(name, handler);
  }

  /** Execute a skill by name, routing all tool calls through the hook pipeline. */
  async executeSkill(session: Session, input: SkillInput): Promise<SkillOutput> {
    const skill = this.registry.get(input.skillName);
    if (!skill) {
      return {
        skillName: input.skillName,
        success: false,
        data: null,
        error: `Skill "${input.skillName}" not found in registry`,
        toolCalls: [],
        durationMs: 0,
      };
    }

    // Check that all required tools are available
    for (const toolName of skill.requiredTools) {
      if (!this.tools.has(toolName)) {
        return {
          skillName: input.skillName,
          success: false,
          data: null,
          error: `Required tool "${toolName}" is not registered`,
          toolCalls: [],
          durationMs: 0,
        };
      }
    }

    // Build a tool invoker that routes through the hook pipeline
    const toolCalls: ToolOutput[] = [];
    const invoker = async (toolInput: ToolInput): Promise<ToolOutput> => {
      const output = await this.invokeTool(session, toolInput);
      toolCalls.push(output);
      return output;
    };

    const start = Date.now();
    try {
      const result = await skill.execute(input.params, invoker);
      result.toolCalls = toolCalls;
      result.durationMs = Date.now() - start;

      this.sessions.record(session, SessionEventType.SkillCompleted, {
        skill: input.skillName,
        success: result.success,
        durationMs: result.durationMs,
        toolCallCount: toolCalls.length,
      });

      return result;
    } catch (err) {
      const durationMs = Date.now() - start;
      this.sessions.record(session, SessionEventType.Error, {
        skill: input.skillName,
        error: String(err),
        durationMs,
      });
      return {
        skillName: input.skillName,
        success: false,
        data: null,
        error: String(err),
        toolCalls,
        durationMs,
      };
    }
  }

  /**
   * Invoke a single tool through the full hook pipeline:
   * pre-hooks → execute (with retries) → post-hooks.
   */
  private async invokeTool(session: Session, input: ToolInput): Promise<ToolOutput> {
    // --- Pre-hooks ---
    const preResult = await this.hooks.runPreHooks({
      sessionId: session.id,
      agentId: session.agentId,
      permissionTier: session.permissionTier,
      toolInput: input,
      metadata: {},
    });

    if (preResult.denied) {
      this.sessions.record(session, SessionEventType.PreHookDenied, {
        tool: input.toolName,
        reason: preResult.reason,
        deniedBy: preResult.deniedBy,
      });
      return {
        toolName: input.toolName,
        success: false,
        data: null,
        error: `Denied by hook "${preResult.deniedBy}": ${preResult.reason}`,
        durationMs: 0,
      };
    }

    // Use potentially rewritten input from hooks
    const finalInput = preResult.rewrittenInput ?? input;

    // --- Execute with retries ---
    this.sessions.record(session, SessionEventType.ToolInvoked, {
      tool: finalInput.toolName,
      params: finalInput.params,
    });

    const start = Date.now();
    let lastError: string | undefined;
    let output: ToolOutput | undefined;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        output = await this.executeWithTimeout(finalInput);
        if (output.success) break;
        lastError = output.error;
      } catch (err) {
        lastError = String(err);
      }

      if (attempt < this.config.maxRetries) {
        const delay = this.config.retryBaseMs * Math.pow(2, attempt);
        await sleep(delay);
      }
    }

    if (!output || !output.success) {
      output = {
        toolName: finalInput.toolName,
        success: false,
        data: null,
        error: lastError ?? "Unknown error after retries",
        durationMs: Date.now() - start,
      };
    }

    this.sessions.record(session, SessionEventType.ToolCompleted, {
      tool: finalInput.toolName,
      success: output.success,
      durationMs: output.durationMs,
      error: output.error,
    });

    // --- Post-hooks ---
    await this.hooks.runPostHooks({
      sessionId: session.id,
      agentId: session.agentId,
      permissionTier: session.permissionTier,
      toolInput: finalInput,
      toolOutput: output,
      metadata: {},
    });

    return output;
  }

  private async executeWithTimeout(input: ToolInput): Promise<ToolOutput> {
    const handler = this.tools.get(input.toolName);
    if (!handler) {
      return {
        toolName: input.toolName,
        success: false,
        data: null,
        error: `Tool "${input.toolName}" not registered`,
        durationMs: 0,
      };
    }

    const start = Date.now();

    const result = await Promise.race([
      handler(input.params),
      sleep(this.config.toolTimeoutMs).then(() => {
        throw new Error(`Tool "${input.toolName}" timed out after ${this.config.toolTimeoutMs}ms`);
      }),
    ]);

    return {
      toolName: input.toolName,
      success: true,
      data: result,
      durationMs: Date.now() - start,
    };
  }
}

/** A tool handler receives params and returns raw data. */
export type ToolHandler = (params: Record<string, unknown>) => Promise<unknown>;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
