"use client";

import { ConversionWidget } from "@/components/conversion/conversion-widget";
import { Flame, Shield, Zap } from "lucide-react";

export default function ConvertPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900">Convert CHA</h1>
        <p className="mt-3 text-gray-500 max-w-xl mx-auto">
          Convert your Charity Coin into Cause Tokens. 95% of CHA is burned
          permanently while funding verified charitable causes.
        </p>
      </div>

      <ConversionWidget />

      <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3 max-w-4xl mx-auto">
        <div className="text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-secondary-100 text-secondary-700 mx-auto mb-3">
            <Flame className="h-6 w-6" />
          </div>
          <h3 className="font-semibold text-gray-900">Deflationary Burn</h3>
          <p className="mt-1 text-sm text-gray-500">
            95% of converted CHA is permanently burned, reducing total supply
            and increasing scarcity.
          </p>
        </div>
        <div className="text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 text-primary-700 mx-auto mb-3">
            <Shield className="h-6 w-6" />
          </div>
          <h3 className="font-semibold text-gray-900">Verified Causes</h3>
          <p className="mt-1 text-sm text-gray-500">
            All causes are vetted and verified. Charity wallets receive funds
            directly on-chain with full transparency.
          </p>
        </div>
        <div className="text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-700 mx-auto mb-3">
            <Zap className="h-6 w-6" />
          </div>
          <h3 className="font-semibold text-gray-900">Instant Settlement</h3>
          <p className="mt-1 text-sm text-gray-500">
            Conversions settle in a single transaction on Base. Low gas fees
            and fast confirmation times.
          </p>
        </div>
      </div>
    </div>
  );
}
