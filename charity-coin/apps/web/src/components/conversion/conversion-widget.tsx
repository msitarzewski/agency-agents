"use client";

import { useState } from "react";
import { useAccount } from "wagmi";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { formatUnits } from "viem";
import {
  ArrowDown,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, CAUSES, FEE_BREAKDOWN, type CauseInfo } from "@/lib/utils";
import { useConversion } from "@/hooks/useConversion";
import { CAUSE_TOKEN_ADDRESSES } from "@/lib/contracts";

interface ConversionWidgetProps {
  defaultCause?: string;
  className?: string;
}

export function ConversionWidget({
  defaultCause,
  className,
}: ConversionWidgetProps) {
  const { isConnected } = useAccount();
  const [amount, setAmount] = useState("");
  const [selectedCause, setSelectedCause] = useState<CauseInfo | null>(
    defaultCause ? CAUSES.find((c) => c.symbol === defaultCause) || null : null
  );

  const causeTokenAddress = selectedCause
    ? CAUSE_TOKEN_ADDRESSES[selectedCause.symbol]
    : undefined;

  const {
    convert,
    balance,
    isApproving,
    isConverting,
    isSuccess,
    error,
    txHash,
    reset,
  } = useConversion(
    causeTokenAddress as `0x${string}` | undefined,
    amount ? parseFloat(amount) : 0
  );

  const formattedBalance = balance
    ? parseFloat(formatUnits(balance, 18)).toLocaleString(undefined, {
        maximumFractionDigits: 2,
      })
    : "0";

  const numAmount = parseFloat(amount) || 0;
  const burnAmount = numAmount * (FEE_BREAKDOWN.burnPercent / 100);
  const charityFee = numAmount * (FEE_BREAKDOWN.charityBps / 10000);
  const liquidityFee = numAmount * (FEE_BREAKDOWN.liquidityBps / 10000);
  const opsFee = numAmount * (FEE_BREAKDOWN.opsBps / 10000);
  const causeTokensOut = burnAmount;

  const handleConvert = () => {
    if (!selectedCause || numAmount <= 0) return;
    convert();
  };

  const handleMax = () => {
    if (balance) {
      setAmount(formatUnits(balance, 18));
    }
  };

  const handleReset = () => {
    setAmount("");
    reset();
  };

  if (isSuccess) {
    return (
      <Card className={cn("max-w-md mx-auto", className)}>
        <CardContent className="p-8 text-center">
          <CheckCircle2 className="h-16 w-16 text-primary-600 mx-auto mb-4" aria-hidden="true" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Conversion Successful!
          </h3>
          <p className="text-gray-500 mb-4">
            You converted {amount} CHA to {selectedCause?.name} tokens.{" "}
            {burnAmount.toFixed(2)} CHA was burned forever.
          </p>
          {txHash && (
            <a
              href={`https://basescan.org/tx/${txHash}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary-700 hover:underline mb-4"
            >
              View on BaseScan <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          )}
          <div className="mt-4">
            <Button onClick={handleReset} variant="outline">
              Convert More
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("max-w-md mx-auto", className)}>
      <CardHeader>
        <CardTitle>Convert CHA</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Amount Input */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label
              htmlFor="cha-amount"
              className="block text-sm font-medium text-gray-700"
            >
              CHA Amount
            </label>
            {isConnected && (
              <span className="text-xs text-gray-500">
                Balance: {formattedBalance} CHA
              </span>
            )}
          </div>
          <div className="relative">
            <input
              id="cha-amount"
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              min="0"
              step="any"
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-lg font-medium text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            />
            <button
              type="button"
              onClick={handleMax}
              aria-label="Set maximum CHA amount"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200"
            >
              MAX
            </button>
          </div>
          {numAmount > 0 && numAmount < 1 && (
            <p className="text-xs text-amber-600 mt-1">
              Minimum conversion: 1 CHA
            </p>
          )}
        </div>

        <div className="flex justify-center">
          <ArrowDown className="h-5 w-5 text-gray-400" aria-hidden="true" />
        </div>

        {/* Cause Selector */}
        <div>
          <label
            htmlFor="cause-select"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Select Cause
          </label>
          <select
            id="cause-select"
            value={selectedCause?.symbol || ""}
            onChange={(e) => {
              const cause = CAUSES.find((c) => c.symbol === e.target.value);
              setSelectedCause(cause || null);
            }}
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          >
            <option value="">Choose a cause...</option>
            {CAUSES.map((cause) => (
              <option key={cause.symbol} value={cause.symbol}>
                {cause.name} ({cause.symbol})
              </option>
            ))}
          </select>
        </div>

        {/* Fee Breakdown */}
        {numAmount > 0 && selectedCause && (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-2">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              Conversion Breakdown
            </h4>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">CHA to Burn (95%)</span>
              <span className="font-medium text-secondary-600">
                {burnAmount.toFixed(2)} CHA
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Charity Fee (2.5%)</span>
              <span className="text-gray-700">{charityFee.toFixed(2)} CHA</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Liquidity Fee (1.5%)</span>
              <span className="text-gray-700">
                {liquidityFee.toFixed(2)} CHA
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Ops Fee (1.0%)</span>
              <span className="text-gray-700">{opsFee.toFixed(2)} CHA</span>
            </div>
            <div className="border-t border-gray-200 pt-2 flex justify-between text-sm font-semibold">
              <span className="text-gray-700">Cause Tokens Received</span>
              <span className="text-primary-700">
                {causeTokensOut.toFixed(2)} {selectedCause.symbol}
              </span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div
            className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 p-3"
            role="alert"
          >
            <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" aria-hidden="true" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Action Button */}
        {!isConnected ? (
          <div className="flex justify-center">
            <ConnectButton />
          </div>
        ) : (
          <Button
            onClick={handleConvert}
            disabled={!selectedCause || numAmount < 1}
            isLoading={isApproving || isConverting}
            className="w-full"
            size="lg"
          >
            {isApproving
              ? "Approving CHA..."
              : isConverting
                ? "Converting..."
                : "Convert CHA"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
