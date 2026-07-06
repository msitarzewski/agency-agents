import i18n from '@/i18n';
import { memo, useCallback, useEffect, useState } from "react";
import {
  Activity,
  Power,
  PlugZap,
  ShieldCheck,
  Clock,
  Loader2,
  ChevronDown,
  CircleDot,
  CircleSlash,
  OctagonX,
} from "lucide-react";
import { toast } from "sonner";
import {
  api,
  type LiveStatus,
  type LiveBrokerStatus,
  type LiveMandateLimits,
  type LiveAuthorizeResponse,
} from "@/lib/api";

interface Props {
  /** Shared `GET /live/status` snapshot, polled once by the parent (Agent.tsx).
   * `null` until the first poll resolves. */
  status: LiveStatus | null;
  /** True when the status endpoint is not wired on this backend (404/501) — hide. */
  unavailable?: boolean;
  /** When true, every broker's halted banner reflects the global kill switch. */
  halted?: boolean;
  /** Forces the parent to re-poll immediately (e.g. after a runner start/stop). */
  onRefresh: () => void;
}

function formatUsd(value: number | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function formatRelative(value: string | number | null | undefined): string {
  if (value == null || value === "") return "never";
  const then = typeof value === "number"
    ? (value < 1_000_000_000_000 ? value * 1000 : value)
    : new Date(value).getTime();
  if (!Number.isFinite(then)) return "unknown";
  const deltaSec = Math.round((Date.now() - then) / 1000);
  if (deltaSec < 0) return "just now";
  if (deltaSec < 60) return `${deltaSec}s ago`;
  if (deltaSec < 3600) return `${Math.floor(deltaSec / 60)}m ago`;
  if (deltaSec < 86_400) return `${Math.floor(deltaSec / 3600)}h ago`;
  return `${Math.floor(deltaSec / 86_400)}d ago`;
}

function formatCountdown(iso: string | undefined): { label: string; expired: boolean; soon: boolean } {
  if (!iso) return { label: "—", expired: false, soon: false };
  const target = new Date(iso).getTime();
  if (!Number.isFinite(target)) return { label: "unknown", expired: false, soon: false };
  const deltaSec = Math.round((target - Date.now()) / 1000);
  if (deltaSec <= 0) return { label: "expired", expired: true, soon: false };
  const days = Math.floor(deltaSec / 86_400);
  const hours = Math.floor((deltaSec % 86_400) / 3600);
  const minutes = Math.floor((deltaSec % 3600) / 60);
  const soon = deltaSec < 86_400;
  if (days > 0) return { label: `${days}d ${hours}h`, expired: false, soon };
  if (hours > 0) return { label: `${hours}h ${minutes}m`, expired: false, soon };
  return { label: `${minutes}m`, expired: false, soon };
}

function summarizeLimits(limits: LiveMandateLimits | undefined): string {
  if (!limits) return "";
  const parts: string[] = [];
  if (limits.max_order_notional_usd != null) parts.push(`≤${formatUsd(limits.max_order_notional_usd)}/order`);
  if (limits.max_trades_per_day != null) parts.push(`${limits.max_trades_per_day}/day`);
  if (limits.max_leverage != null) parts.push(limits.max_leverage <= 1 ? "no leverage" : `${limits.max_leverage}×`);
  return parts.join(" · ");
}

function fallbackAuthorizeInstruction(): string {
  return "Run `vibe-trading connector list`, choose the broker profile, then run `vibe-trading connector authorize <profile>` from the desktop session that will hold the broker connection.";
}

function BrokerRow({
  broker,
  halted,
  onRefresh,
}: {
  broker: LiveBrokerStatus;
  halted: boolean;
  onRefresh: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [authorizeHint, setAuthorizeHint] = useState<LiveAuthorizeResponse | null>(null);
  const [authorizeFailed, setAuthorizeFailed] = useState(false);
  const brokerKey = broker.auth.broker;
  const authorized = broker.auth.oauth_token_present;
  const runnerAlive = broker.runner?.alive ?? false;
  const mandate = broker.mandate ?? null;
  const countdown = formatCountdown(mandate?.expires_at);
  const authorizeInstruction = authorizeHint?.instruction
    ?? (authorizeFailed ? fallbackAuthorizeInstruction() : "Loading connector authorization instructions...");
  const authorizeNote = "The connector channel stays read-only until OAuth succeeds and a mandate is committed.";

  useEffect(() => {
    let cancelled = false;
    setAuthorizeHint(null);
    setAuthorizeFailed(false);
    if (authorized || !brokerKey) return () => { cancelled = true; };

    api.authorizeLive(brokerKey)
      .then((response) => {
        if (!cancelled) setAuthorizeHint(response);
      })
      .catch(() => {
        if (!cancelled) setAuthorizeFailed(true);
      });

    return () => { cancelled = true; };
  }, [authorized, brokerKey]);

  const toggleRunner = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      if (runnerAlive) {
        await api.stopLiveRunner(brokerKey);
        toast.success(`Runner stopped for ${brokerKey}`);
      } else {
        await api.startLiveRunner(brokerKey);
        toast.success(`Runner started for ${brokerKey}`);
      }
      onRefresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Runner control failed.");
    } finally {
      setBusy(false);
    }
  }, [brokerKey, busy, runnerAlive, onRefresh]);

  return (
    <div className="grid gap-2 rounded-lg border bg-muted/20 p-2.5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="truncate text-xs font-semibold capitalize text-foreground">{brokerKey}</span>
          {authorized ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-2.5 w-2.5" />
              Authorized
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
              <CircleSlash className="h-2.5 w-2.5" />
              Not connected
            </span>
          )}
        </div>
      </div>

      {/* Connect-profile on-ramp for unauthorized brokers (C2). The OAuth bootstrap
          is a desktop-only CLI step (SPEC §4 headless behavior), so the web surface
          surfaces the discoverable instruction rather than driving the browser flow. */}
      {!authorized ? (
        <div className="grid gap-1.5 rounded-md border border-dashed border-primary/30 bg-primary/5 p-2">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-primary">
            <PlugZap className="h-3 w-3 shrink-0" />
            Connect this profile to enable connector runtime
          </div>
          <p className="text-[10px] leading-relaxed text-muted-foreground">
            {authorizeInstruction}
          </p>
          {authorizeNote && (
            <p className="text-[10px] leading-relaxed text-muted-foreground">
              {authorizeNote}
            </p>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-md border bg-background/60 p-2">
              <div className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                <CircleDot className={["h-2.5 w-2.5", runnerAlive ? "text-emerald-500" : "text-muted-foreground"].join(" ")} />
                Runner
              </div>
              <div className={["mt-0.5 text-xs font-semibold", runnerAlive ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"].join(" ")}>
                {runnerAlive ? "Running" : "Stopped"}
              </div>
            </div>
            <div className="rounded-md border bg-background/60 p-2">
              <div className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                <Activity className="h-2.5 w-2.5" />
                Last tick
              </div>
              <div className="mt-0.5 text-xs font-medium text-foreground">
                {formatRelative(broker.runner?.last_tick)}
              </div>
            </div>
          </div>

          {mandate ? (
            <div className="rounded-md border bg-background/60 p-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  <ShieldCheck className="h-2.5 w-2.5" />
                  Active mandate
                </div>
                {mandate.expires_at && (
                  <span
                    className={[
                      "inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium",
                      countdown.expired
                        ? "bg-destructive/10 text-destructive"
                        : countdown.soon
                          ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                          : "bg-muted text-muted-foreground",
                    ].join(" ")}
                    title={`Expires ${new Date(mandate.expires_at).toLocaleString()}`}
                  >
                    <Clock className="h-2.5 w-2.5" />
                    {countdown.expired ? "expired" : `expires in ${countdown.label}`}
                  </span>
                )}
              </div>
              <div className="mt-0.5 font-mono text-[11px] text-foreground">
                {summarizeLimits(mandate.limits) || "limits unavailable"}
              </div>
            </div>
          ) : (
            <div className="rounded-md border border-dashed bg-background/40 p-2 text-[10px] text-muted-foreground">
              No active mandate. Ask the agent to propose one, then commit it before starting the connector runtime.
            </div>
          )}

          <div className="flex items-center justify-between gap-2">
            {halted ? (
              <span className="inline-flex items-center gap-1 text-[10px] font-medium text-destructive">
                <OctagonX className="h-3 w-3" />
                Halted — runner controls disabled
              </span>
            ) : (
              <span className="text-[10px] text-muted-foreground">
                {runnerAlive ? "Runtime active inside mandate" : "Idle"}
              </span>
            )}
            <button
              type="button"
              onClick={toggleRunner}
              disabled={busy || halted || !mandate}
              className={[
                "inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-[11px] font-medium transition-colors disabled:opacity-40",
                runnerAlive
                  ? "border-destructive/40 text-destructive hover:bg-destructive/10"
                  : "border-primary/40 text-primary hover:bg-primary/10",
              ].join(" ")}
              title={runnerAlive ? "Stop the persistent runner" : "Start the persistent runner"}
            >
              {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Power className="h-3 w-3" />}
              {runnerAlive ? "Stop runner" : "Start runner"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Persistent live-runtime status panel (SPEC §7.5 + audit C2).
 *
 * Renders the shared `GET /live/status` snapshot (polled once by Agent.tsx and passed
 * in as `status`, so the kill switch and this panel share a single poller). Per authorized
 * profile: runner running state, last heartbeat tick, the active mandate's limits, and an
 * expiry countdown. `onRefresh` asks the parent to re-poll after a runner start/stop. Unauthorized
 * profiles get a connector on-ramp so a web user can discover how to enable connector
 * runtime execution. Runner start/stop are privileged surface fetches (`api.startLiveRunner` /
 * `api.stopLiveRunner`), never chat messages. Collapses to a compact toggle.
 */
export const RunnerStatus = memo(function RunnerStatus({ status, unavailable, halted, onRefresh }: Props) {
  const [open, setOpen] = useState(false);

  if (unavailable) return null;
  if (!status || status.brokers.length === 0) return null;

  const isHalted = halted ?? status.global_halted;
  const anyRunning = status.brokers.some((b) => b.runner?.alive);
  const authorizedCount = status.brokers.filter((b) => b.auth.oauth_token_present).length;

  return (
    <div className="grid gap-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex max-w-full items-center gap-1.5 justify-self-start rounded-lg bg-primary/10 px-2.5 py-1 text-left text-xs font-medium text-primary transition-colors hover:bg-primary/15"
        aria-label={i18n.t("runnerStatus.connectorRuntime")}
        aria-expanded={open}
      >
        <Activity className="h-3 w-3 shrink-0" />
        <span className="shrink-0">{i18n.t("runnerStatus.connectorRuntime")}</span>
        <span className="truncate text-muted-foreground">
          {authorizedCount > 0 ? i18n.t("runnerStatus.connected", { count: authorizedCount }) : i18n.t("runnerStatus.noConnector")}
        </span>
        {anyRunning && !isHalted && (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
            <CircleDot className="h-2.5 w-2.5" />
            {i18n.t("runnerStatus.running")}
          </span>
        )}
        {isHalted && (
          <span className="inline-flex items-center gap-1 rounded-full bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium text-destructive">
            <OctagonX className="h-2.5 w-2.5" />
            {i18n.t("runnerStatus.halted")}
          </span>
        )}
        <ChevronDown className={["h-3 w-3 shrink-0 transition-transform", open ? "rotate-180" : ""].join(" ")} aria-hidden="true" />
      </button>

      {open && (
        <div className="grid gap-2 rounded-xl border border-primary/20 bg-background/95 p-3 shadow-sm">
          {status.brokers.map((broker) => (
            <BrokerRow key={broker.auth.broker} broker={broker} halted={isHalted || broker.halted} onRefresh={onRefresh} />
          ))}
        </div>
      )}
    </div>
  );
});
