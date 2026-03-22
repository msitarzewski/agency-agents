"use client";

import { useState, useCallback } from "react";
import {
  useAccount,
  useWriteContract,
  useWaitForTransactionReceipt,
  useReadContract,
} from "wagmi";
import { parseUnits } from "viem";
import { waitForTransactionReceipt } from "wagmi/actions";
import { config } from "@/lib/wagmi";
import {
  CONTRACT_ADDRESSES,
  CHARITY_COIN_ABI,
  CONVERSION_ENGINE_ABI,
} from "@/lib/contracts";

export function useConversion(
  causeTokenAddress: `0x${string}` | undefined,
  amount: number
) {
  const { address } = useAccount();
  const [step, setStep] = useState<
    "idle" | "approving" | "waiting_approval" | "converting"
  >("idle");
  const [error, setError] = useState<string | null>(null);
  const [txHash, setTxHash] = useState<`0x${string}` | undefined>(undefined);
  const [isSuccess, setIsSuccess] = useState(false);

  const parsedAmount = amount > 0 ? parseUnits(amount.toString(), 18) : 0n;

  // Check current allowance
  const { data: allowance } = useReadContract({
    address: CONTRACT_ADDRESSES.CharityCoin,
    abi: CHARITY_COIN_ABI,
    functionName: "allowance",
    args: address
      ? [address, CONTRACT_ADDRESSES.ConversionEngine]
      : undefined,
    query: {
      enabled: !!address && parsedAmount > 0n,
    },
  });

  // Read user's CHA balance
  const { data: balance } = useReadContract({
    address: CONTRACT_ADDRESSES.CharityCoin,
    abi: CHARITY_COIN_ABI,
    functionName: "balanceOf",
    args: address ? [address] : undefined,
    query: {
      enabled: !!address,
    },
  });

  const { writeContractAsync } = useWriteContract();

  const { isLoading: isWaitingForTx } = useWaitForTransactionReceipt({
    hash: txHash,
    query: {
      enabled: !!txHash,
    },
  });

  const convert = useCallback(async () => {
    if (!address || !causeTokenAddress || parsedAmount <= 0n) {
      setError("Invalid conversion parameters");
      return;
    }

    // Check balance before attempting conversion
    const userBalance = (balance as bigint) ?? 0n;
    if (userBalance < parsedAmount) {
      setError("Insufficient CHA balance");
      return;
    }

    setError(null);

    try {
      // Step 1: Check if approval is needed
      const currentAllowance = (allowance as bigint) ?? 0n;

      if (currentAllowance < parsedAmount) {
        setStep("approving");

        const approveTx = await writeContractAsync({
          address: CONTRACT_ADDRESSES.CharityCoin,
          abi: CHARITY_COIN_ABI,
          functionName: "approve",
          args: [CONTRACT_ADDRESSES.ConversionEngine, parsedAmount],
        });

        setTxHash(approveTx);
        setStep("waiting_approval");

        // Wait for approval confirmation before proceeding
        await waitForTransactionReceipt(config, { hash: approveTx });
      }

      // Step 2: Execute conversion
      setStep("converting");

      const convertTx = await writeContractAsync({
        address: CONTRACT_ADDRESSES.ConversionEngine,
        abi: CONVERSION_ENGINE_ABI,
        functionName: "convert",
        args: [causeTokenAddress, parsedAmount],
      });

      setTxHash(convertTx);
      setIsSuccess(true);
      setStep("idle");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Transaction failed";
      if (message.includes("User rejected") || message.includes("user rejected")) {
        setError("Transaction was cancelled");
      } else if (message.includes("insufficient") || message.includes("exceeds balance")) {
        setError("Insufficient balance for this transaction");
      } else if (message.includes("AmountTooSmall")) {
        setError("Minimum conversion amount is 1 CHA");
      } else {
        setError(message);
      }
      setStep("idle");
    }
  }, [address, causeTokenAddress, parsedAmount, allowance, balance, writeContractAsync]);

  const reset = useCallback(() => {
    setStep("idle");
    setError(null);
    setTxHash(undefined);
    setIsSuccess(false);
  }, []);

  return {
    convert,
    balance: balance as bigint | undefined,
    isApproving: step === "approving" || step === "waiting_approval",
    isConverting: step === "converting" || (step === "converting" && isWaitingForTx),
    isSuccess,
    error,
    txHash,
    reset,
  };
}
