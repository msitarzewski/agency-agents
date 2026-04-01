// ---------------------------------------------------------------------------
// Kuro-7 Agent Harness — Entry Point
//
// Wires all six architectural patterns into a running agent:
//   1. Tool Orchestration (orchestrator → executor → stream)
//   2. Hook System (pre/post interception pipeline)
//   3. Skill Registry (dynamic capability map)
//   4. Session Persistence (full decision chain)
//   5. Permission System (tiered access control)
//   6. Transport Layer (CLI, webhook, websocket)
// ---------------------------------------------------------------------------

import { PermissionTier, type AgentConfig } from "./types/index.js";

// Core
import { Orchestrator } from "./core/orchestrator.js";
import { Executor } from "./core/executor.js";
import { StreamManager } from "./core/stream.js";
import { HookPipeline } from "./core/hooks.js";
import { SkillRegistry } from "./core/registry.js";
import { SessionManager } from "./core/session.js";
import { PermissionSystem } from "./core/permissions.js";
import { TransportRouter } from "./core/transport.js";

// Skills
import { swapSkill } from "./skills/swap.js";
import { riskAssessSkill } from "./skills/risk-assess.js";
import { portfolioScanSkill } from "./skills/portfolio-scan.js";
import { whaleTrackSkill } from "./skills/whale-track.js";

// Tools
import { jupiterTools } from "./tools/jupiter.js";
import { heliusTools } from "./tools/helius.js";
import { birdeyeTools } from "./tools/birdeye.js";
import { dexscreenerTools } from "./tools/dexscreener.js";
import { solanaTools } from "./tools/solana.js";

// Hooks
import {
  createRugProtectionHook,
  createPositionLimitHook,
  createSimulationGateHook,
  createRateLimitHook,
  createAuditLogHook,
} from "./hooks/safety.js";

// Transports
import { CliTransport } from "./transports/cli.js";
import { WebhookTransport } from "./transports/webhook.js";

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

function loadConfig(): AgentConfig {
  return {
    agentId: "kuro-7",
    name: "Kuro-7",
    personaPath: "../specialized/kuro-7-solana-trader.md",
    defaultPermissionTier: PermissionTier.Standard,
    rpcUrl: process.env.SOLANA_RPC_URL ?? "https://api.mainnet-beta.solana.com",
    heliusApiKey: process.env.HELIUS_API_KEY ?? "",
    birdeyeApiKey: process.env.BIRDEYE_API_KEY ?? "",
    maxPositionPct: Number(process.env.MAX_POSITION_PCT ?? 5),
    maxDrawdownPct: Number(process.env.MAX_DRAWDOWN_PCT ?? 15),
    defaultSlippageBps: Number(process.env.DEFAULT_SLIPPAGE_BPS ?? 50),
    priorityFee: (process.env.PRIORITY_FEE_STRATEGY as "auto" | "fixed") ?? "auto",
    priorityFeeLamports: Number(process.env.PRIORITY_FEE_LAMPORTS ?? 10_000),
  };
}

export function createHarness(configOverrides?: Partial<AgentConfig>) {
  const config = { ...loadConfig(), ...configOverrides };

  // --- Pattern 4: Session Persistence ---
  const sessions = new SessionManager();

  // --- Pattern 1c: Streaming ---
  const stream = new StreamManager();

  // --- Pattern 2: Hook Pipeline ---
  const hooks = new HookPipeline();

  // --- Pattern 5: Permission System ---
  const permissions = new PermissionSystem();

  // Register tool permission requirements
  const allToolDefs = [
    ...jupiterTools.definitions,
    ...heliusTools.definitions,
    ...birdeyeTools.definitions,
    ...dexscreenerTools.definitions,
    ...solanaTools.definitions,
  ];
  permissions.registerTools(allToolDefs);

  // Permission hook (priority 10 — runs first)
  hooks.register(permissions.toHook());

  // Safety hooks
  let portfolioValueUsd = 0;

  hooks.register(createRugProtectionHook({
    minLiquidityUsd: 50_000,
    blockMintAuthority: true,
  }));

  hooks.register(createPositionLimitHook({
    maxPositionPct: config.maxPositionPct,
    getPortfolioValueUsd: () => portfolioValueUsd,
  }));

  hooks.register(createSimulationGateHook());

  hooks.register(createRateLimitHook({
    maxCalls: 60,
    windowMs: 60_000,
  }));

  // Audit log (post-hook)
  hooks.register(createAuditLogHook());

  // --- Pattern 3: Skill Registry ---
  const registry = new SkillRegistry();
  registry.register(swapSkill);
  registry.register(riskAssessSkill);
  registry.register(portfolioScanSkill);
  registry.register(whaleTrackSkill);

  // --- Pattern 1b: Executor ---
  const executor = new Executor(hooks, registry, sessions, {
    maxRetries: 3,
    retryBaseMs: 500,
    toolTimeoutMs: 30_000,
  });

  // Register tool handlers
  for (const [name, handler] of Object.entries(jupiterTools.handlers)) {
    executor.registerTool(name, handler);
  }
  for (const [name, handler] of Object.entries(dexscreenerTools.handlers)) {
    executor.registerTool(name, handler);
  }

  // API-key-dependent handlers
  if (config.heliusApiKey) {
    const heliusHandlers = heliusTools.createHandlers(config.heliusApiKey);
    for (const [name, handler] of Object.entries(heliusHandlers)) {
      executor.registerTool(name, handler);
    }
  }
  if (config.birdeyeApiKey) {
    const birdeyeHandlers = birdeyeTools.createHandlers(config.birdeyeApiKey);
    for (const [name, handler] of Object.entries(birdeyeHandlers)) {
      executor.registerTool(name, handler);
    }
  }

  // Solana RPC handlers
  const solanaHandlers = solanaTools.createHandlers(config.rpcUrl);
  for (const [name, handler] of Object.entries(solanaHandlers)) {
    executor.registerTool(name, handler);
  }

  // --- Pattern 1a: Orchestrator ---
  const orchestrator = new Orchestrator(registry, executor, sessions, stream);

  // --- Pattern 6: Transport Router ---
  const transports = new TransportRouter();

  // CLI transport (default)
  transports.register("cli", new CliTransport());

  // Webhook transport (optional, configured via env)
  if (process.env.WEBHOOK_URL) {
    transports.register("webhook", new WebhookTransport({
      url: process.env.WEBHOOK_URL,
      authHeader: process.env.WEBHOOK_AUTH,
    }));
  }

  return {
    config,
    orchestrator,
    executor,
    sessions,
    stream,
    hooks,
    registry,
    permissions,
    transports,

    /** Start the agent — listen on all transports and route to orchestrator. */
    start() {
      console.log(`\n⚡ Kuro-7 online | ${config.rpcUrl}`);
      console.log(`  Skills: ${registry.list().map((s) => s.name).join(", ")}`);
      console.log(`  Hooks: ${hooks.list().map((h) => h.name).join(", ")}`);
      console.log(`  Transports: ${transports.channels().join(", ")}`);
      console.log(`  Permission tier: ${config.defaultPermissionTier}`);
      console.log(`  Max position: ${config.maxPositionPct}% | Max drawdown: ${config.maxDrawdownPct}%`);
      console.log();

      const cleanup = transports.listenAll(async (message) => {
        const session = sessions.create(config.agentId, config.defaultPermissionTier);
        message.sessionId = session.id;

        const response = await orchestrator.handle(session, message);
        await transports.send(response);
      });

      return cleanup;
    },

    /** Update the cached portfolio value (called after portfolio scans). */
    setPortfolioValue(usd: number) {
      portfolioValueUsd = usd;
    },
  };
}

// -- CLI entrypoint ---------------------------------------------------------

const isMainModule = process.argv[1]?.endsWith("index.ts") || process.argv[1]?.endsWith("index.js");
if (isMainModule) {
  const harness = createHarness();
  harness.start();
}

// -- Exports ----------------------------------------------------------------

export { Orchestrator } from "./core/orchestrator.js";
export { Executor } from "./core/executor.js";
export { StreamManager } from "./core/stream.js";
export { HookPipeline } from "./core/hooks.js";
export { SkillRegistry } from "./core/registry.js";
export { SessionManager } from "./core/session.js";
export { PermissionSystem } from "./core/permissions.js";
export { TransportRouter } from "./core/transport.js";
export * from "./types/index.js";
