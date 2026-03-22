"use client";

import Link from "next/link";
import {
  Heart,
  GraduationCap,
  TreePine,
  Droplets,
  Wheat,
  type LucideIcon,
} from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ImpactMeter } from "@/components/ui/impact-meter";
import { cn, causeColors } from "@/lib/utils";

const ICON_MAP: Record<string, LucideIcon> = {
  Heart,
  GraduationCap,
  TreePine,
  Droplets,
  Wheat,
};

export interface CauseCardProps {
  name: string;
  symbol: string;
  description: string;
  slug: string;
  totalRaised: number;
  totalBurned: number;
  goal: number;
  icon: string;
}

export function CauseCard({
  name,
  symbol,
  description,
  slug,
  totalRaised,
  totalBurned,
  goal,
  icon,
}: CauseCardProps) {
  const colors = causeColors[symbol] || causeColors.HEALTH;
  const IconComponent = ICON_MAP[icon] || Heart;

  return (
    <Card
      className={cn(
        "group relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1",
        `border-l-4`,
        colors.border
      )}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex h-10 w-10 items-center justify-center rounded-xl",
                colors.light
              )}
            >
              <IconComponent className={cn("h-5 w-5", colors.text)} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{name}</h3>
              <span
                className={cn(
                  "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
                  colors.badge
                )}
              >
                ${symbol}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <p className="text-sm text-gray-500 mb-4">{description}</p>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="rounded-lg bg-gray-50 p-3">
            <p className="text-xs text-gray-400">Total Raised</p>
            <p className="text-lg font-semibold text-gray-900">
              {totalRaised.toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-3">
            <p className="text-xs text-gray-400">CHA Burned</p>
            <p className="text-lg font-semibold text-secondary-600">
              {totalBurned.toLocaleString()}
            </p>
          </div>
        </div>

        <ImpactMeter
          current={totalRaised}
          goal={goal}
          label="Progress"
          color={colors.bg}
        />
      </CardContent>

      <CardFooter className="gap-2">
        <Link href={`/causes/${slug}`} className="flex-1">
          <Button variant="outline" className="w-full" size="sm">
            Details
          </Button>
        </Link>
        <Link href={`/convert?cause=${symbol}`} className="flex-1">
          <Button className="w-full" size="sm">
            Convert
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}
