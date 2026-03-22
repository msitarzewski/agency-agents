"use client";

import { useReadContract } from "wagmi";
import {
  CONTRACT_ADDRESSES,
  CAUSE_TOKEN_FACTORY_ABI,
  CAUSE_TOKEN_ADDRESSES,
} from "@/lib/contracts";
import { CAUSES, type CauseInfo } from "@/lib/utils";

export interface CauseData extends CauseInfo {
  tokenAddress: `0x${string}`;
  isActive: boolean;
  totalRaised: number;
  totalBurned: number;
  goal: number;
}

/**
 * Hook to fetch all causes.
 * Currently returns static data; in production, reads from CauseTokenFactory contract.
 */
export function useCauses() {
  const { data: causeCount, isLoading: isLoadingCount } = useReadContract({
    address: CONTRACT_ADDRESSES.CauseTokenFactory,
    abi: CAUSE_TOKEN_FACTORY_ABI,
    functionName: "getCauseCount",
  });

  // Static cause data for development / demo purposes
  const causes: CauseData[] = CAUSES.map((cause) => ({
    ...cause,
    tokenAddress: (CAUSE_TOKEN_ADDRESSES[cause.symbol] ||
      "0x0000000000000000000000000000000000000000") as `0x${string}`,
    isActive: true,
    totalRaised: getPlaceholderRaised(cause.symbol),
    totalBurned: getPlaceholderBurned(cause.symbol),
    goal: getPlaceholderGoal(cause.symbol),
  }));

  return {
    causes,
    causeCount: causeCount ? Number(causeCount) : causes.length,
    isLoading: isLoadingCount,
  };
}

// Placeholder data for demo
function getPlaceholderRaised(symbol: string): number {
  const map: Record<string, number> = {
    HEALTH: 245000,
    EDU: 189000,
    ENV: 312000,
    WATER: 156000,
    HUNGER: 278000,
  };
  return map[symbol] || 100000;
}

function getPlaceholderBurned(symbol: string): number {
  const map: Record<string, number> = {
    HEALTH: 232750,
    EDU: 179550,
    ENV: 296400,
    WATER: 148200,
    HUNGER: 264100,
  };
  return map[symbol] || 95000;
}

function getPlaceholderGoal(symbol: string): number {
  const map: Record<string, number> = {
    HEALTH: 500000,
    EDU: 400000,
    ENV: 500000,
    WATER: 300000,
    HUNGER: 400000,
  };
  return map[symbol] || 500000;
}
