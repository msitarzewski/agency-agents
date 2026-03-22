"use client";

import { useState } from "react";
import { Search, TrendingUp, Flame, Users } from "lucide-react";
import { CauseCard } from "@/components/causes/cause-card";
import { useCauses } from "@/hooks/useCauses";

export default function CausesPage() {
  const { causes } = useCauses();
  const [searchQuery, setSearchQuery] = useState("");

  const filteredCauses = causes.filter(
    (cause) =>
      cause.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cause.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cause.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalRaised = causes.reduce((sum, c) => sum + c.totalRaised, 0);
  const totalBurned = causes.reduce((sum, c) => sum + c.totalBurned, 0);
  const totalSupporters = 2847; // Placeholder

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900">All Causes</h1>
        <p className="mt-2 text-gray-500">
          Browse and support verified charitable causes. Every conversion burns
          CHA and creates impact.
        </p>
      </div>

      {/* Impact Summary */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <TrendingUp className="h-5 w-5 text-primary-700" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Raised</p>
            <p className="text-xl font-bold text-gray-900">
              {totalRaised.toLocaleString()} CHA
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary-100">
            <Flame className="h-5 w-5 text-secondary-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Burned</p>
            <p className="text-xl font-bold text-secondary-600">
              {totalBurned.toLocaleString()} CHA
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-100">
            <Users className="h-5 w-5 text-accent-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Supporters</p>
            <p className="text-xl font-bold text-gray-900">
              {totalSupporters.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="mb-8">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search causes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          />
        </div>
      </div>

      {/* Causes Grid */}
      {filteredCauses.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredCauses.map((cause) => (
            <CauseCard
              key={cause.symbol}
              name={cause.name}
              symbol={cause.symbol}
              description={cause.description}
              slug={cause.slug}
              totalRaised={cause.totalRaised}
              totalBurned={cause.totalBurned}
              goal={cause.goal}
              icon={cause.icon}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-12 text-center">
          <p className="text-gray-500">
            No causes found matching &quot;{searchQuery}&quot;
          </p>
        </div>
      )}
    </div>
  );
}
