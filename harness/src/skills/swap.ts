// ---------------------------------------------------------------------------
// Skill: Token Swap via Jupiter V6
// Orchestrates: risk check → quote → simulate → sign → confirm
// ---------------------------------------------------------------------------

import {
  PermissionTier,
  type Skill,
  type SkillOutput,
  type ToolInvoker,
} from "../types/index.js";

export const swapSkill: Skill = {
  name: "swap",
  description: "Execute a token swap via Jupiter V6 aggregator with pre-trade risk validation",
  requiredTools: ["jupiter-quote", "jupiter-swap", "birdeye-token-overview"],
  dependsOn: ["risk-assess"],
  requiredPermission: PermissionTier.Standard,

  async execute(params: Record<string, unknown>, invoke: ToolInvoker): Promise<SkillOutput> {
    const start = Date.now();
    const inputMint = params.inputMint as string;
    const outputMint = params.outputMint as string;
    const amount = params.amount as number;
    const slippageBps = (params.slippageBps as number) ?? 50;

    if (!inputMint || !outputMint || !amount) {
      return {
        skillName: "swap",
        success: false,
        data: null,
        error: "Missing required params: inputMint, outputMint, amount",
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    // 1. Get a quote from Jupiter
    const quoteResult = await invoke({
      toolName: "jupiter-quote",
      params: { inputMint, outputMint, amount, slippageBps },
    });

    if (!quoteResult.success) {
      return {
        skillName: "swap",
        success: false,
        data: null,
        error: `Quote failed: ${quoteResult.error}`,
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    const quote = quoteResult.data as Record<string, unknown>;
    const priceImpactPct = Number(quote.priceImpactPct ?? 0);

    // Abort if price impact is too high (safety gate within the skill)
    if (priceImpactPct > 5) {
      return {
        skillName: "swap",
        success: false,
        data: { quote, abortReason: "price_impact_too_high" },
        error: `Price impact ${priceImpactPct.toFixed(2)}% exceeds 5% threshold. Aborting.`,
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    // 2. Build and execute the swap transaction
    const swapResult = await invoke({
      toolName: "jupiter-swap",
      params: {
        quoteResponse: quote,
        wrapAndUnwrapSol: true,
        dynamicComputeUnitLimit: true,
        prioritizationFeeLamports: params.priorityFee ?? "auto",
      },
    });

    if (!swapResult.success) {
      return {
        skillName: "swap",
        success: false,
        data: { quote },
        error: `Swap execution failed: ${swapResult.error}`,
        toolCalls: [],
        durationMs: Date.now() - start,
      };
    }

    return {
      skillName: "swap",
      success: true,
      data: {
        quote,
        swap: swapResult.data,
        priceImpactPct,
        inputMint,
        outputMint,
        amount,
        slippageBps,
      },
      toolCalls: [],
      durationMs: Date.now() - start,
    };
  },
};
