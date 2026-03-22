"use client";

import { cn } from "@/lib/utils";

interface ImpactMeterProps {
  current: number;
  goal: number;
  label?: string;
  color?: string;
  className?: string;
}

export function ImpactMeter({
  current,
  goal,
  label,
  color = "bg-primary-600",
  className,
}: ImpactMeterProps) {
  const percentage = Math.min((current / goal) * 100, 100);

  return (
    <div className={cn("w-full", className)}>
      {label && (
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <span className="text-sm text-gray-500">
            {percentage.toFixed(1)}%
          </span>
        </div>
      )}

      <div
        className="relative h-3 w-full overflow-hidden rounded-full bg-gray-100"
        role="progressbar"
        aria-valuenow={Math.round(percentage)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label || "Impact progress"}
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-1000 ease-out",
            color
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="mt-1 flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {current.toLocaleString()} CHA
        </span>
        <span className="text-xs text-gray-500">
          {goal.toLocaleString()} CHA
        </span>
      </div>
    </div>
  );
}
