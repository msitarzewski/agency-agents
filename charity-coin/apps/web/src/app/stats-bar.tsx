"use client";

import { Flame, DollarSign, Users } from "lucide-react";
import { BurnCounter } from "@/components/ui/burn-counter";

export function StatsBar() {
  // Placeholder stats - in production these would come from contract reads
  const stats = {
    totalBurned: 1121000,
    totalRaised: 1180000,
    activeCauses: 5,
  };

  return (
    <section className="relative -mt-8 z-10">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <BurnCounter totalBurned={stats.totalBurned} />

          <div className="flex flex-col items-center justify-center rounded-2xl bg-white border border-gray-200 p-8 shadow-sm">
            <DollarSign className="h-8 w-8 text-primary-600 mb-2" />
            <span className="text-4xl font-bold text-gray-900 tabular-nums">
              ${(stats.totalRaised / 1000).toFixed(0)}K
            </span>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">
              Total Raised for Charity
            </p>
          </div>

          <div className="flex flex-col items-center justify-center rounded-2xl bg-white border border-gray-200 p-8 shadow-sm">
            <Users className="h-8 w-8 text-accent-600 mb-2" />
            <span className="text-4xl font-bold text-gray-900 tabular-nums">
              {stats.activeCauses}
            </span>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">
              Active Causes
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
