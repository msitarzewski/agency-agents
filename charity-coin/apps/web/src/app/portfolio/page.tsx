"use client";

import { useTokenBalances } from "@/hooks/useTokenBalances";
import { useAccount } from "wagmi";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { causeColors } from "@/lib/utils";
import { Wallet, TrendingUp, Flame } from "lucide-react";

export default function PortfolioPage() {
  const { isConnected } = useAccount();
  const { chaBalance, causeBalances, totalImpactFormatted, isLoading } =
    useTokenBalances();

  if (!isConnected) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8 text-center">
        <Wallet className="h-16 w-16 text-gray-300 mx-auto mb-6" />
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          Connect Your Wallet
        </h1>
        <p className="text-gray-500 mb-8 max-w-md mx-auto">
          Connect your wallet to view your CHA balance, cause token holdings,
          and impact history.
        </p>
        <ConnectButton />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Portfolio</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3 mb-10">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100 text-primary-700">
                <Wallet className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">CHA Balance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {isLoading ? "..." : chaBalance.formatted}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Impact</p>
                <p className="text-2xl font-bold text-gray-900">
                  {isLoading ? "..." : totalImpactFormatted}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary-100 text-secondary-700">
                <Flame className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Causes Supported</p>
                <p className="text-2xl font-bold text-gray-900">
                  {causeBalances.filter((b) => b.balance > 0n).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cause Token Holdings */}
      <Card>
        <CardHeader>
          <CardTitle>Cause Token Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-gray-100">
            {causeBalances.map((token) => {
              const colors = causeColors[token.symbol];
              return (
                <div
                  key={token.symbol}
                  className="flex items-center justify-between py-4 first:pt-0 last:pb-0"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors?.badge || "bg-gray-100 text-gray-800"}`}
                    >
                      {token.symbol}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {token.name}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-gray-700">
                    {isLoading ? "..." : token.formatted}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Transaction History Placeholder */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 text-center py-8">
            Transaction history will appear here once you make your first
            conversion.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
