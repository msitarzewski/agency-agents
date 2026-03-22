"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Heart,
  GraduationCap,
  TreePine,
  Droplets,
  Wheat,
  ArrowLeft,
  TrendingUp,
  Flame,
  Users,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ImpactMeter } from "@/components/ui/impact-meter";
import { ConversionWidget } from "@/components/conversion/conversion-widget";
import { getCauseBySlug, causeColors, shortenAddress } from "@/lib/utils";
import { cn } from "@/lib/utils";

const ICON_MAP: Record<string, LucideIcon> = {
  Heart,
  GraduationCap,
  TreePine,
  Droplets,
  Wheat,
};

// Placeholder leaderboard data
const LEADERBOARD = [
  { address: "0x1234567890abcdef1234567890abcdef12345678", amount: 45000, conversions: 12 },
  { address: "0xabcdef1234567890abcdef1234567890abcdef12", amount: 32000, conversions: 8 },
  { address: "0x9876543210fedcba9876543210fedcba98765432", amount: 28500, conversions: 15 },
  { address: "0xfedcba9876543210fedcba9876543210fedcba98", amount: 21000, conversions: 6 },
  { address: "0x1111222233334444555566667777888899990000", amount: 15000, conversions: 4 },
];

// Placeholder recent conversions
const RECENT_CONVERSIONS = [
  { address: "0x1234567890abcdef1234567890abcdef12345678", amount: 5000, time: "2 min ago" },
  { address: "0xabcdef1234567890abcdef1234567890abcdef12", amount: 2500, time: "15 min ago" },
  { address: "0x9876543210fedcba9876543210fedcba98765432", amount: 10000, time: "1 hr ago" },
  { address: "0xfedcba9876543210fedcba9876543210fedcba98", amount: 750, time: "3 hrs ago" },
  { address: "0x1111222233334444555566667777888899990000", amount: 3200, time: "5 hrs ago" },
];

// Placeholder stats per cause
const CAUSE_STATS: Record<string, { totalRaised: number; totalBurned: number; supporters: number; goal: number }> = {
  health: { totalRaised: 245000, totalBurned: 232750, supporters: 612, goal: 500000 },
  education: { totalRaised: 189000, totalBurned: 179550, supporters: 487, goal: 400000 },
  environment: { totalRaised: 312000, totalBurned: 296400, supporters: 823, goal: 500000 },
  water: { totalRaised: 156000, totalBurned: 148200, supporters: 398, goal: 300000 },
  hunger: { totalRaised: 278000, totalBurned: 264100, supporters: 527, goal: 400000 },
};

export default function CauseDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const cause = getCauseBySlug(slug);

  if (!cause) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-gray-900">Cause Not Found</h1>
        <p className="mt-2 text-gray-500">
          The cause you are looking for does not exist.
        </p>
        <Link href="/causes" className="mt-6 inline-block">
          <Button>
            <ArrowLeft className="h-4 w-4" /> Back to Causes
          </Button>
        </Link>
      </div>
    );
  }

  const colors = causeColors[cause.symbol] || causeColors.HEALTH;
  const IconComponent = ICON_MAP[cause.icon] || Heart;
  const stats = CAUSE_STATS[slug] || CAUSE_STATS.health;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Back link */}
      <Link
        href="/causes"
        className="mb-6 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Causes
      </Link>

      {/* Cause Hero */}
      <div
        className={cn(
          "rounded-2xl border-l-4 bg-gradient-to-r from-gray-50 to-white p-8 mb-8",
          colors.border
        )}
      >
        <div className="flex items-start gap-4">
          <div
            className={cn(
              "flex h-14 w-14 items-center justify-center rounded-2xl",
              colors.light
            )}
          >
            <IconComponent className={cn("h-7 w-7", colors.text)} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{cause.name}</h1>
            <span
              className={cn(
                "inline-block mt-1 rounded-full px-3 py-0.5 text-sm font-medium",
                colors.badge
              )}
            >
              ${cause.symbol}
            </span>
            <p className="mt-3 text-gray-500 max-w-2xl">{cause.description}</p>
          </div>
        </div>
      </div>

      {/* Impact Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-8">
        <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <TrendingUp className="h-5 w-5 text-primary-700" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Raised</p>
            <p className="text-xl font-bold text-gray-900">
              {stats.totalRaised.toLocaleString()} CHA
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary-100">
            <Flame className="h-5 w-5 text-secondary-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">CHA Burned</p>
            <p className="text-xl font-bold text-secondary-600">
              {stats.totalBurned.toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-100">
            <Users className="h-5 w-5 text-accent-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Supporters</p>
            <p className="text-xl font-bold text-gray-900">
              {stats.supporters.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left: Conversion + Progress */}
        <div className="lg:col-span-1 space-y-6">
          <ConversionWidget defaultCause={cause.symbol} />

          <Card>
            <CardContent className="p-6">
              <ImpactMeter
                current={stats.totalRaised}
                goal={stats.goal}
                label="Cause Goal Progress"
                color={colors.bg}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right: Leaderboard + Recent */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Converters */}
          <Card>
            <CardHeader>
              <CardTitle>Top Converters</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="pb-3 text-left font-medium text-gray-500">
                        Rank
                      </th>
                      <th className="pb-3 text-left font-medium text-gray-500">
                        Address
                      </th>
                      <th className="pb-3 text-right font-medium text-gray-500">
                        Total Converted
                      </th>
                      <th className="pb-3 text-right font-medium text-gray-500">
                        Conversions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {LEADERBOARD.map((entry, index) => (
                      <tr key={entry.address}>
                        <td className="py-3 text-gray-900 font-medium">
                          #{index + 1}
                        </td>
                        <td className="py-3 font-mono text-gray-600">
                          {shortenAddress(entry.address)}
                        </td>
                        <td className="py-3 text-right font-medium text-gray-900">
                          {entry.amount.toLocaleString()} CHA
                        </td>
                        <td className="py-3 text-right text-gray-500">
                          {entry.conversions}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Recent Conversions */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Conversions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {RECENT_CONVERSIONS.map((tx, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-primary-500" />
                      <span className="font-mono text-sm text-gray-600">
                        {shortenAddress(tx.address)}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {tx.amount.toLocaleString()} CHA
                      </p>
                      <p className="text-xs text-gray-400">{tx.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
