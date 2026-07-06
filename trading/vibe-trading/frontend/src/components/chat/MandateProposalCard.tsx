import i18n from '@/i18n';
import { memo, useCallback, useState } from "react";
import { ShieldCheck, ShieldAlert, Wallet, OctagonX, SlidersHorizontal, Check, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api, type MandateProfile, type MandateProposal } from "@/lib/api";
import { AgentAvatar } from "./AgentAvatar";

interface Props {
  proposal: MandateProposal;
  /** True once a mandate.committed event for this proposal has arrived; the card collapses to a badge. */
  committed?: {
    selected_ordinal?: number;
    max_order_usd?: number;
    daily_trade_cap?: number;
    expires_at?: string;
  } | null;
  /**
   * Submit a free-text adjust request as a normal chat message back to the agent,
   * which re-invokes propose_mandate_profiles and returns a fresh proposal.
   */
  onAdjust: (message: string) => void;
}

function formatUsd(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function formatLeverage(leverage: MandateProfile["leverage"]): string {
  if (typeof leverage === "number") {
    return leverage <= 1 ? "no leverage" : `${leverage}× leverage`;
  }
  const lowered = leverage.toLowerCase();
  return lowered === "none" || lowered === "" ? "no leverage" : leverage;
}

function formatUniverse(universe: MandateProfile["universe"]): string {
  if (Array.isArray(universe)) return universe.join(" / ");
  return universe.replace(/_/g, " ");
}

function ProfileTile({
  profile,
  active,
  busy,
  disabled,
  adjusting,
  onCommit,
  onAdjustToggle,
  onAdjustSubmit,
  onAdjustCancel,
}: {
  profile: MandateProfile;
  active: boolean;
  busy: boolean;
  disabled: boolean;
  adjusting: boolean;
  onCommit: () => void;
  onAdjustToggle: () => void;
  onAdjustSubmit: (text: string) => void;
  onAdjustCancel: () => void;
}) {
  const [adjustText, setAdjustText] = useState("");

  const submit = () => {
    const text = adjustText.trim();
    if (!text) return;
    onAdjustSubmit(text);
    setAdjustText("");
  };

  return (
    <div
      className={[
        "rounded-xl border p-3 transition-colors",
        active
          ? "border-primary/60 bg-primary/5"
          : "border-border/60 bg-muted/20 hover:border-primary/40",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 font-mono text-[11px] font-semibold text-primary">
            {profile.ordinal}
          </span>
          <span className="text-sm font-semibold text-foreground">{profile.label}</span>
        </div>
        <button
          type="button"
          onClick={onAdjustToggle}
          disabled={disabled}
          className="inline-flex items-center gap-1 rounded-lg border px-2 py-0.5 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-40"
          title={i18n.t("mandate.adjustTitle")}
        >
          <SlidersHorizontal className="h-3 w-3" />
          {i18n.t("mandate.adjust")}
        </button>
      </div>

      <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
        <div className="col-span-2">
          <dt className="text-muted-foreground">{i18n.t("mandate.universe")}</dt>
          <dd className="font-medium text-foreground">{formatUniverse(profile.universe)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">{i18n.t("mandate.maxOrder")}</dt>
          <dd className="font-mono font-medium text-foreground">{formatUsd(profile.max_order_usd)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">{i18n.t("mandate.dailyCap")}</dt>
          <dd className="font-mono font-medium text-foreground">{profile.daily_trade_cap} trades/day</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">{i18n.t("mandate.leverage")}</dt>
          <dd className="font-medium text-foreground">{formatLeverage(profile.leverage)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">{i18n.t("mandate.instruments")}</dt>
          <dd className="font-medium text-foreground">{profile.instruments.join(", ") || "—"}</dd>
        </div>
      </dl>

      {profile.notes && (
        <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">{profile.notes}</p>
      )}

      {adjusting ? (
        <div className="mt-3 grid gap-2">
          <input
            type="text"
            value={adjustText}
            autoFocus
            onChange={(e) => setAdjustText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                submit();
              } else if (e.key === "Escape") {
                onAdjustCancel();
              }
            }}
            placeholder={i18n.t("mandate.adjustPlaceholder")}
            className="w-full rounded-lg border bg-background px-3 py-1.5 text-xs text-foreground outline-none focus:ring-2 focus:ring-primary/30"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onAdjustCancel}
              className="inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              <X className="h-3 w-3" />
              Cancel
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={!adjustText.trim()}
              className="inline-flex items-center gap-1 rounded-lg bg-primary px-2 py-1 text-[11px] font-medium text-primary-foreground transition-opacity disabled:opacity-40"
            >
              <Check className="h-3 w-3" />
              Send adjustment
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={onCommit}
          disabled={disabled}
          className="mt-3 inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />}
          {busy ? "Committing…" : `Commit “${profile.label}”`}
        </button>
      )}
    </div>
  );
}

/**
 * Renders a connector-runtime mandate proposal (SPEC Consent §1/§2).
 *
 * Each profile tile shows concrete numbers (universe, max order, daily cap, leverage,
 * instruments). Committing calls `api.commitMandate` — a privileged surface action,
 * never `api.sendMessage`. "Adjust" sends a natural-language message back to the agent
 * to re-render a fresh proposal. Once committed, the card collapses to a compact badge.
 */
export const MandateProposalCard = memo(function MandateProposalCard({ proposal, committed, onAdjust }: Props) {
  const [busyOrdinal, setBusyOrdinal] = useState<number | null>(null);
  const [adjustingOrdinal, setAdjustingOrdinal] = useState<number | null>(null);

  const handleCommit = useCallback(
    async (ordinal: number) => {
      if (busyOrdinal != null) return;
      const broker = proposal.account?.broker?.trim().toLowerCase();
      if (!broker) {
        toast.error("Cannot commit mandate: connector broker is missing. Ask the agent to regenerate the proposal.");
        return;
      }
      setBusyOrdinal(ordinal);
      try {
        await api.commitMandate({
          broker,
          proposal_id: proposal.proposal_id,
          selected_ordinal: ordinal,
          adjustments: null,
          consent_ack: true,
          session_id: proposal.session_id,
        });
        // Card collapses to the active-mandate badge when the mandate.committed
        // SSE event arrives; no optimistic state-write here.
      } catch (error) {
        setBusyOrdinal(null);
        toast.error(error instanceof Error ? error.message : "Failed to commit mandate.");
      }
    },
    [busyOrdinal, proposal.account?.broker, proposal.proposal_id, proposal.session_id],
  );

  // Collapsed state: a compact active-mandate badge (same visual family as the goal badge).
  if (committed) {
    const profile = proposal.profiles.find((p) => p.ordinal === committed.selected_ordinal);
    const maxOrder = committed.max_order_usd ?? profile?.max_order_usd;
    const dailyCap = committed.daily_trade_cap ?? profile?.daily_trade_cap;
    const expires = committed.expires_at ? new Date(committed.expires_at) : null;
    return (
      <div className="flex gap-3">
        <AgentAvatar />
        <div className="flex-1 min-w-0">
          <span className="inline-flex max-w-full flex-wrap items-center gap-1.5 rounded-lg bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="h-3 w-3 shrink-0" />
            <span className="shrink-0">
              Mandate {committed.selected_ordinal != null ? `#${committed.selected_ordinal} ` : ""}active
            </span>
            {maxOrder != null && (
              <span className="shrink-0 font-mono text-[11px]">· ≤{formatUsd(maxOrder)}/order</span>
            )}
            {dailyCap != null && <span className="shrink-0 font-mono text-[11px]">· {dailyCap}/day</span>}
            {expires && (
              <span className="shrink-0 text-[10px] text-muted-foreground">
                · expires {expires.toLocaleDateString()}
              </span>
            )}
          </span>
        </div>
      </div>
    );
  }

  const isReauth = Boolean(proposal.reauth_for);

  return (
    <div className="flex gap-3">
      <AgentAvatar />
      <div className="flex-1 min-w-0 space-y-3 rounded-2xl border border-primary/20 bg-background/95 p-4 shadow-sm">
        <div className="flex items-start gap-2">
          {isReauth ? (
            <ShieldAlert className="h-4 w-4 shrink-0 text-amber-500" />
          ) : (
            <ShieldCheck className="h-4 w-4 shrink-0 text-primary" />
          )}
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground">
              {isReauth ? i18n.t("mandate.reauthMandate") : i18n.t("mandate.runtimeMandate")}
            </p>
            {proposal.intent_normalized && (
              <p className="text-xs text-muted-foreground">{proposal.intent_normalized}</p>
            )}
            {proposal.account && (
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                {proposal.account.broker} · {proposal.account.type} account · funded by {proposal.account.funded_by}
              </p>
            )}
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {proposal.profiles.map((profile) => (
            <ProfileTile
              key={profile.ordinal}
              profile={profile}
              active={adjustingOrdinal === profile.ordinal}
              busy={busyOrdinal === profile.ordinal}
              disabled={busyOrdinal != null}
              adjusting={adjustingOrdinal === profile.ordinal}
              onCommit={() => handleCommit(profile.ordinal)}
              onAdjustToggle={() =>
                setAdjustingOrdinal((cur) => (cur === profile.ordinal ? null : profile.ordinal))
              }
              onAdjustCancel={() => setAdjustingOrdinal(null)}
              onAdjustSubmit={(text) => {
                setAdjustingOrdinal(null);
                onAdjust(`For mandate proposal "${profile.label}" (option ${profile.ordinal}): ${text}`);
              }}
            />
          ))}
        </div>

        <div className="grid gap-1.5 border-t border-border/60 pt-2 text-[11px] text-muted-foreground">
          {proposal.funding_note && (
            <p className="flex items-start gap-1.5">
              <Wallet className="mt-0.5 h-3 w-3 shrink-0" />
              <span>{proposal.funding_note}</span>
            </p>
          )}
          {proposal.halt_note && (
            <p className="flex items-start gap-1.5">
              <OctagonX className="mt-0.5 h-3 w-3 shrink-0 text-destructive" />
              <span>{proposal.halt_note}</span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
});
