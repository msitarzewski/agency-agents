// ---------------------------------------------------------------------------
// Foundational types for the Kuro-7 agent harness
// ---------------------------------------------------------------------------

/** Unique identifier (nanoid-style, not UUID — shorter, URL-safe). */
export type Id = string;

// -- Permission tiers -------------------------------------------------------

export enum PermissionTier {
  /** Read-only: query data, never mutate. */
  ReadOnly = "read_only",
  /** Standard: operate within defined parameters. */
  Standard = "standard",
  /** Elevated: high-value actions, requires confirmation. */
  Elevated = "elevated",
  /** Full: unrestricted — emergency override by human operator. */
  Full = "full",
}

// -- Tool system ------------------------------------------------------------

export interface ToolDefinition {
  name: string;
  description: string;
  /** Minimum permission tier required to invoke this tool. */
  requiredPermission: PermissionTier;
  /** JSON-Schema-like shape for tool inputs. */
  inputSchema: Record<string, unknown>;
  /** JSON-Schema-like shape for tool outputs. */
  outputSchema: Record<string, unknown>;
}

export interface ToolInput {
  toolName: string;
  params: Record<string, unknown>;
}

export interface ToolOutput {
  toolName: string;
  success: boolean;
  data: unknown;
  error?: string;
  durationMs: number;
}

// -- Hook system ------------------------------------------------------------

export enum HookPhase {
  PreToolUse = "pre_tool_use",
  PostToolUse = "post_tool_use",
}

export interface HookContext {
  sessionId: Id;
  agentId: Id;
  permissionTier: PermissionTier;
  toolInput: ToolInput;
  /** Only present in post-hooks. */
  toolOutput?: ToolOutput;
  /** Arbitrary metadata from earlier hooks in the chain. */
  metadata: Record<string, unknown>;
}

export enum HookVerdict {
  /** Allow execution to proceed. */
  Allow = "allow",
  /** Deny execution — fail closed. */
  Deny = "deny",
  /** Rewrite the request (mutated context continues down the chain). */
  Rewrite = "rewrite",
}

export interface HookResult {
  verdict: HookVerdict;
  reason?: string;
  /** If verdict is Rewrite, the mutated context replaces the original. */
  rewrittenContext?: Partial<HookContext>;
}

export interface Hook {
  name: string;
  phase: HookPhase;
  /** Lower number = higher priority (runs first). */
  priority: number;
  execute(ctx: HookContext): Promise<HookResult>;
}

// -- Skill registry ---------------------------------------------------------

export interface SkillDefinition {
  name: string;
  description: string;
  /** Tools this skill requires to function. */
  requiredTools: string[];
  /** Other skills this skill depends on. */
  dependsOn: string[];
  /** Minimum permission tier required to invoke this skill. */
  requiredPermission: PermissionTier;
}

export interface SkillInput {
  skillName: string;
  params: Record<string, unknown>;
}

export interface SkillOutput {
  skillName: string;
  success: boolean;
  data: unknown;
  error?: string;
  /** Tool calls made during skill execution. */
  toolCalls: ToolOutput[];
  durationMs: number;
}

export interface Skill extends SkillDefinition {
  execute(
    params: Record<string, unknown>,
    invoker: ToolInvoker,
  ): Promise<SkillOutput>;
}

/** Function provided to skills so they can call tools through the harness. */
export type ToolInvoker = (input: ToolInput) => Promise<ToolOutput>;

// -- Session persistence ----------------------------------------------------

export interface SessionEvent {
  id: Id;
  sessionId: Id;
  timestamp: number;
  type: SessionEventType;
  payload: unknown;
}

export enum SessionEventType {
  /** Inbound request received. */
  RequestReceived = "request_received",
  /** Orchestrator decomposed task into subtasks. */
  TaskDecomposed = "task_decomposed",
  /** Skill selected for a subtask. */
  SkillSelected = "skill_selected",
  /** Pre-hook fired. */
  PreHookFired = "pre_hook_fired",
  /** Pre-hook denied an action. */
  PreHookDenied = "pre_hook_denied",
  /** Tool invoked. */
  ToolInvoked = "tool_invoked",
  /** Tool returned result. */
  ToolCompleted = "tool_completed",
  /** Post-hook fired. */
  PostHookFired = "post_hook_fired",
  /** Skill completed. */
  SkillCompleted = "skill_completed",
  /** Agent decided NOT to take an action (and why). */
  ActionSkipped = "action_skipped",
  /** Final response produced. */
  ResponseProduced = "response_produced",
  /** Error occurred. */
  Error = "error",
}

export interface Session {
  id: Id;
  agentId: Id;
  createdAt: number;
  events: SessionEvent[];
  /** Current permission tier for this session. */
  permissionTier: PermissionTier;
  /** Arbitrary key-value state carried across the session. */
  state: Record<string, unknown>;
}

// -- Transport layer --------------------------------------------------------

export interface TransportMessage {
  sessionId: Id;
  content: string;
  /** Structured data payload alongside the human-readable content. */
  structured?: Record<string, unknown>;
  /** Where this message should be routed. */
  channel: string;
}

export interface Transport {
  name: string;
  /** Send a message out through this transport. */
  send(message: TransportMessage): Promise<void>;
  /** Start listening for inbound messages (returns cleanup function). */
  listen(handler: (message: TransportMessage) => Promise<void>): () => void;
}

// -- Orchestrator -----------------------------------------------------------

export interface Task {
  id: Id;
  description: string;
  skillName: string;
  params: Record<string, unknown>;
  status: "pending" | "running" | "completed" | "failed" | "denied";
  result?: SkillOutput;
  error?: string;
}

export interface OrchestrationPlan {
  tasks: Task[];
  /** Tasks that can run in parallel share the same phase number. */
  phases: Map<number, Id[]>;
}

// -- Agent config -----------------------------------------------------------

export interface AgentConfig {
  agentId: Id;
  name: string;
  /** Path to the persona markdown file. */
  personaPath: string;
  defaultPermissionTier: PermissionTier;
  /** Solana RPC endpoint. */
  rpcUrl: string;
  /** Helius API key. */
  heliusApiKey: string;
  /** Birdeye API key. */
  birdeyeApiKey: string;
  /** Maximum portfolio percentage per trade (0-100). */
  maxPositionPct: number;
  /** Maximum portfolio drawdown before halting (0-100). */
  maxDrawdownPct: number;
  /** Default slippage in basis points. */
  defaultSlippageBps: number;
  /** Priority fee strategy. */
  priorityFee: "auto" | "fixed";
  /** Fixed priority fee in lamports (when strategy is "fixed"). */
  priorityFeeLamports: number;
}
