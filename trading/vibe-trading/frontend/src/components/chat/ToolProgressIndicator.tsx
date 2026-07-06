import { useRef, type JSX } from "react";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { ProgressBar } from "@/components/chat/ProgressBar";
import { localizeToolName } from "@/lib/tools";
import type { ToolCallEntry } from "@/types/agent";

/* ---------- ETA tracking (per-tool) ---------- */
interface EtaSample {
  stage: string;
  current: number;
  suppressed: boolean;
}

/* ---------- Determinate progress ring ---------- */
interface RingProps {
  current: number;
  total: number;
}

function ProgressRing({ current, total }: RingProps): JSX.Element {
  // h-3 w-3 = 12px; viewBox 24, r=10, circumference = 2*PI*10 ≈ 62.83
  const pct = Math.min(1, Math.max(0, current / total));
  const c = 2 * Math.PI * 10;
  const dash = c * pct;
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-3 w-3 text-primary shrink-0"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.2"
        strokeWidth="3"
      />
      <circle
        cx="12"
        cy="12"
        r="10"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${c - dash}`}
        transform="rotate(-90 12 12)"
        style={{ transition: "stroke-dasharray 200ms ease" }}
      />
    </svg>
  );
}

/* ---------- Single tool row ---------- */
interface RowProps {
  entry: ToolCallEntry;
  stepIndex: number;
  totalSteps: number;
  isHeader?: boolean;
  connector?: "branch" | "end" | "none";
  eta: number | null;
}

function ToolRow({ entry, stepIndex, totalSteps, isHeader, connector = "none", eta }: RowProps): JSX.Element {
  const progress = entry.progress;
  const hasDeterminate = !!(progress && typeof progress.current === "number" && typeof progress.total === "number" && progress.total > 0);
  const stage = progress?.stage || "";
  const message = progress?.message || "";

  const icon = entry.status === "error"
    ? <XCircle className="h-3 w-3 text-danger shrink-0" />
    : entry.status === "ok"
      ? <CheckCircle2 className="h-3 w-3 text-success shrink-0" />
      : hasDeterminate
        ? <ProgressRing current={progress!.current!} total={progress!.total!} />
        : <Loader2 className="h-3 w-3 animate-spin text-primary shrink-0" />;

  const localized = localizeToolName(entry.tool);
  const stepLabel = isHeader
    ? `${totalSteps} tools running`
    : `Step ${stepIndex} · ${localized}`;

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-x-2 gap-y-0.5 text-xs min-w-0">
      {/* Primary row */}
      <div className="flex items-center gap-2 min-w-0 sm:flex-none">
        {connector !== "none" && (
          <span className="text-border/60 shrink-0 w-3 text-center" aria-hidden="true">
            {connector === "branch" ? "├" : "└"}
          </span>
        )}
        {icon}
        <span className="text-foreground truncate">{stepLabel}</span>
        {entry.elapsed_s != null && (
          <span className="ml-auto sm:ml-0 tabular-nums text-[10px] text-muted-foreground/70 shrink-0">
            {entry.elapsed_s.toFixed(0)}s
          </span>
        )}
      </div>
      {/* Secondary row: stage + progress bar (+ ETA) */}
      {(progress && (hasDeterminate || stage)) && (
        <div className="flex items-center gap-2 min-w-0 sm:flex-1">
          {stage && (
            <span className="text-foreground text-xs shrink-0 truncate max-w-[40%]">{stage}</span>
          )}
          {hasDeterminate && (
            <ProgressBar
              current={progress!.current!}
              total={progress!.total!}
              height="xs"
              showCount
              ariaLabel={stage || localized}
              className="text-muted-foreground"
            />
          )}
          {eta != null && (
            <span className="text-[10px] text-muted-foreground/70 tabular-nums shrink-0">
              ~{eta}s left
            </span>
          )}
        </div>
      )}
      {/* Tertiary row: message */}
      {message && (
        <div className="text-[10px] text-muted-foreground/60 truncate min-w-0 sm:basis-full">
          {message}
        </div>
      )}
    </div>
  );
}

/* ---------- Public component ---------- */
interface Props {
  /** Full toolCalls slice from the store. The component filters running ones internally. */
  toolCalls: ToolCallEntry[];
}

const MAX_VISIBLE = 3;

export function ToolProgressIndicator({ toolCalls }: Props): JSX.Element | null {
  // Per-tool ETA samples (mutable across renders, not state to avoid re-renders).
  const etaSamplesRef = useRef<Map<string, EtaSample>>(new Map());

  const running = toolCalls.filter((tc) => tc.status === "running");
  if (running.length === 0) return null;

  const totalSoFar = toolCalls.length;

  /* ---------- compute ETA for each running tool ---------- */
  const computeEta = (tc: ToolCallEntry): number | null => {
    const p = tc.progress;
    if (!p || typeof p.current !== "number" || typeof p.total !== "number") return null;
    if (p.total <= 0) return null;
    const stage = p.stage || "";
    const samples = etaSamplesRef.current;
    const prev = samples.get(tc.tool);

    // Out-of-order: current decreased → suppress for the rest of the run.
    if (prev && p.current < prev.current) {
      samples.set(tc.tool, { stage, current: p.current, suppressed: true });
      return null;
    }
    if (prev?.suppressed && prev.stage === stage) {
      // Update tracking but keep suppressed.
      samples.set(tc.tool, { stage, current: p.current, suppressed: true });
      return null;
    }
    samples.set(tc.tool, { stage, current: p.current, suppressed: false });

    // Need a stable stage and enough samples to extrapolate.
    if (!prev || prev.stage !== stage) return null;
    if (p.current < 3) return null;
    if (p.current < p.total * 0.1) return null;
    if (tc.elapsed_s == null || tc.elapsed_s <= 0) return null;

    const eta = (tc.elapsed_s / p.current) * (p.total - p.current);
    if (!isFinite(eta) || eta < 0) return null;
    return Math.round(eta);
  };

  /* ---------- aggregate icon state for the header row ---------- */
  // (Used when 2+ tools are running — header shows multi-tool aggregate.)
  // Note: filtered list is `running` so all are still running by construction.
  // We still inspect entire toolCalls so an earlier error in this turn shows
  // through the aggregate.
  const anyError = toolCalls.some((tc) => tc.status === "error");
  const aggregateIcon = anyError
    ? <XCircle className="h-3 w-3 text-danger shrink-0" />
    : <Loader2 className="h-3 w-3 animate-spin text-primary shrink-0" />;

  // Display rule: ≤3 running → show all; >3 → first 2 + "… +N more".
  const showAll = running.length <= MAX_VISIBLE;
  const rows = showAll ? running : running.slice(0, 2);
  const overflow = showAll ? 0 : running.length - rows.length;

  /* ---------- render ---------- */
  if (running.length === 1) {
    const only = running[0];
    const eta = computeEta(only);
    return (
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="min-w-0"
      >
        <ToolRow
          entry={only}
          stepIndex={totalSoFar}
          totalSteps={running.length}
          eta={eta}
        />
      </div>
    );
  }

  // 2+ running — header + indented rows.
  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className={cn("min-w-0 space-y-1")}
    >
      {/* Header row */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {aggregateIcon}
        <span className="text-foreground">{running.length} tools running</span>
      </div>
      {/* Indented rows */}
      <div className="pl-4 space-y-1">
        {rows.map((tc, i) => (
          <ToolRow
            key={tc.id}
            entry={tc}
            stepIndex={toolCalls.indexOf(tc) + 1}
            totalSteps={running.length}
            connector={i === rows.length - 1 && overflow === 0 ? "end" : "branch"}
            eta={computeEta(tc)}
          />
        ))}
        {overflow > 0 && (
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground/60">
            <span className="text-border/60 shrink-0 w-3 text-center" aria-hidden="true">└</span>
            <span>… +{overflow} more</span>
          </div>
        )}
      </div>
    </div>
  );
}
