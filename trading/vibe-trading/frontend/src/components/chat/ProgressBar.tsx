import type { ReactElement } from "react";
import { cn } from "@/lib/utils";

interface ProgressBarProps {
  /** Current progress value; clamped to [0, total] internally. */
  current: number;
  /** Total value; must be > 0 or the component renders nothing. */
  total: number;
  /** Bar height: "xs" => h-1, "sm" => h-2. Defaults to "xs". */
  height?: "xs" | "sm";
  /** When true, appends "{current}/{total}" text after the bar. */
  showCount?: boolean;
  /** Visible-context label (e.g. "PDF page progress"). */
  ariaLabel?: string;
  /** Extra Tailwind classes for the outer wrapper. */
  className?: string;
}

/**
 * Thin horizontal progress bar primitive.
 *
 * Visual pattern mirrors AlphaZoo's progress bar
 * (`frontend/src/pages/AlphaZoo.tsx:854-859`):
 *   `bg-muted rounded-full overflow-hidden` track + `bg-primary
 *   transition-all duration-300` fill.
 *
 * Accessibility: a native `<progress>` element carries the semantics
 * for assistive technologies; the visual fill div is purely decorative.
 */
export function ProgressBar({
  current,
  total,
  height = "xs",
  showCount = false,
  ariaLabel,
  className,
}: ProgressBarProps): ReactElement | null {
  if (total <= 0) return null;

  const clamped = Math.min(total, Math.max(0, current));
  const pct = Math.min(100, Math.max(0, (clamped / total) * 100));
  const heightClass = height === "sm" ? "h-2" : "h-1";

  return (
    <div
      className={cn("flex items-center gap-2 min-w-0", className)}
      aria-label={ariaLabel}
    >
      <progress
        value={clamped}
        max={total}
        className="sr-only"
        aria-label={ariaLabel}
      />
      <div
        className={cn(
          "bg-muted rounded-full overflow-hidden flex-1",
          heightClass,
        )}
      >
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      {showCount && (
        <span className="text-[10px] text-muted-foreground tabular-nums shrink-0">
          {clamped}/{total}
        </span>
      )}
    </div>
  );
}
