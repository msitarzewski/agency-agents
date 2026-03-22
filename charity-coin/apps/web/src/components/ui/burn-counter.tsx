"use client";

import { useEffect, useState } from "react";
import { Flame } from "lucide-react";
import { cn } from "@/lib/utils";

interface BurnCounterProps {
  totalBurned: number;
  className?: string;
}

export function BurnCounter({ totalBurned, className }: BurnCounterProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    if (hasAnimated) {
      setDisplayValue(totalBurned);
      return;
    }

    const duration = 2000;
    const steps = 60;
    const increment = totalBurned / steps;
    let current = 0;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current = Math.min(current + increment, totalBurned);
      setDisplayValue(Math.floor(current));

      if (step >= steps) {
        clearInterval(timer);
        setDisplayValue(totalBurned);
        setHasAnimated(true);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [totalBurned, hasAnimated]);

  const formattedValue = displayValue.toLocaleString();

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 p-8",
        className
      )}
    >
      {/* Glow effect */}
      <div className="absolute inset-0 rounded-2xl burn-glow opacity-50" />

      <div className="relative z-10 flex flex-col items-center gap-3">
        <div className="flex items-center gap-2">
          <Flame className="h-8 w-8 text-secondary-500 animate-pulse-glow" />
          <span className="text-5xl font-bold text-gray-900 tabular-nums tracking-tight">
            {formattedValue}
          </span>
        </div>
        <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">
          CHA Burned Forever
        </p>
      </div>
    </div>
  );
}
