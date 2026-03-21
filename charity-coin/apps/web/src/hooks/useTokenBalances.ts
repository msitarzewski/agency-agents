"use client";

import { useAccount, useReadContract, useReadContracts } from "wagmi";
import {
  CONTRACT_ADDRESSES,
  CHARITY_COIN_ABI,
  CAUSE_TOKEN_ABI,
  CAUSE_TOKEN_ADDRESSES,
} from "@/lib/contracts";
import { formatCHA, CAUSES } from "@/lib/utils";

export interface TokenBalance {
  symbol: string;
  name: string;
  balance: bigint;
  formatted: string;
  address: `0x${string}`;
}

export function useTokenBalances() {
  const { address, isConnected } = useAccount();

  // Read CHA balance
  const { data: chaBalance, isLoading: isLoadingCHA } = useReadContract({
    address: CONTRACT_ADDRESSES.CharityCoin,
    abi: CHARITY_COIN_ABI,
    functionName: "balanceOf",
    args: address ? [address] : undefined,
    query: {
      enabled: !!address,
    },
  });

  // Read all cause token balances
  const causeTokenContracts = CAUSES.map((cause) => ({
    address: CAUSE_TOKEN_ADDRESSES[cause.symbol] as `0x${string}`,
    abi: CAUSE_TOKEN_ABI,
    functionName: "balanceOf" as const,
    args: address ? [address] : undefined,
  }));

  const { data: causeBalances, isLoading: isLoadingCauses } = useReadContracts({
    contracts: causeTokenContracts,
    query: {
      enabled: !!address,
    },
  });

  // Format CHA balance
  const chaTokenBalance: TokenBalance = {
    symbol: "CHA",
    name: "Charity Coin",
    balance: (chaBalance as bigint) ?? 0n,
    formatted: chaBalance ? formatCHA(chaBalance as bigint) : "0.00",
    address: CONTRACT_ADDRESSES.CharityCoin,
  };

  // Format cause token balances
  const causeTokenBalances: TokenBalance[] = CAUSES.map((cause, index) => {
    const result = causeBalances?.[index];
    const balance =
      result && result.status === "success" ? (result.result as bigint) : 0n;
    return {
      symbol: cause.symbol,
      name: cause.name,
      balance,
      formatted: formatCHA(balance),
      address: CAUSE_TOKEN_ADDRESSES[cause.symbol] as `0x${string}`,
    };
  });

  // Total impact: sum of all cause token balances
  const totalImpact = causeTokenBalances.reduce(
    (sum, token) => sum + token.balance,
    0n
  );

  return {
    isConnected,
    chaBalance: chaTokenBalance,
    causeBalances: causeTokenBalances,
    totalImpact,
    totalImpactFormatted: formatCHA(totalImpact),
    isLoading: isLoadingCHA || isLoadingCauses,
  };
}
