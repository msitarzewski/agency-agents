import i18n from '@/i18n';
/**
 * Alpha Zoo — browse / detail / bench views.
 *
 * Routing model: a single page component, three URL shapes:
 *   /alpha-zoo                 → browse view
 *   /alpha-zoo/bench           → bench runner
 *   /alpha-zoo/:alphaId        → alpha detail
 *
 * The bench view uses a raw EventSource rather than the shared `useSSE` hook
 * because that hook hard-codes the agent's known event types (text_delta,
 * tool_call, …) and would silently drop the alpha bench events
 * (`progress`, `result`, `done`, `error`). The swarm page uses the same
 * raw-EventSource pattern (frontend/src/pages/Agent.tsx).
 */

import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  Layers,
  Search,
  Play,
  ArrowLeft,
  ArrowLeftRight,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Library,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  api,
  type AlphaSummary,
  type AlphaDetailResponse,
  type AlphaBenchResult,
  type AlphaBenchTopRow,
  type AlphaCompareResult,
} from "@/lib/api";
import { echarts } from "@/lib/echarts";
import { getChartTheme } from "@/lib/chart-theme";
import { useDarkMode } from "@/hooks/useDarkMode";

/* ---------- Constants ---------- */

interface ZooCard {
  id: string;
  title: string;
  description: string;
  approxCount: number;
  accent: string;
}

// IMPORTANT: The Kakushadze 101 zoo must use the author's name as the label.
// The legacy / trademark name is forbidden by a CI grep gate — do not add it.
const ZOO_CARDS: ZooCard[] = [
  {
    id: "qlib158",
    title: "Qlib 158",
    description:
      "Microsoft Qlib's full 158-feature library covering momentum, volatility, volume and rolling statistical signals.",
    approxCount: 154,
    accent: "from-sky-500/20 to-sky-500/5",
  },
  {
    id: "alpha101",
    title: "Kakushadze 101 Formulaic Alphas",
    description:
      "The 101 formulaic alphas from Kakushadze (2015); short-horizon cross-sectional signals.",
    approxCount: 101,
    accent: "from-emerald-500/20 to-emerald-500/5",
  },
  {
    id: "gtja191",
    title: "GTJA 191",
    description:
      "Guotai Junan Securities' 191 alphas; technical and microstructure signals tuned to China A-share markets.",
    approxCount: 191,
    accent: "from-amber-500/20 to-amber-500/5",
  },
  {
    id: "academic",
    title: "Academic Anomalies",
    description:
      "Curated long-horizon anomalies from the academic literature (value, momentum, quality, low-vol, etc.).",
    approxCount: 6,
    accent: "from-violet-500/20 to-violet-500/5",
  },
];

const UNIVERSE_OPTIONS = [
  { value: "csi300", label: "CSI 300 (China A)" },
  { value: "sp500", label: "S&P 500 (US)" },
  { value: "btc-usdt", label: "BTC-USDT (Crypto)" },
];

const PAGE_SIZE = 50;

/* ---------- Helpers ---------- */

function fmtNum(v: unknown, digits = 3): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

function metaString(meta: Record<string, unknown>, key: string): string {
  const v = meta[key];
  if (v === undefined || v === null || v === "") return "—";
  if (Array.isArray(v)) return v.join(", ");
  return String(v);
}

/* ---------- Page entry ---------- */

export function AlphaZoo() {
  const params = useParams<{ alphaId?: string }>();
  const { pathname } = useLocation();

  // Internal view selection
  if (pathname === "/alpha-zoo/bench") {
    return <BenchView />;
  }
  if (pathname === "/alpha-zoo/compare") {
    return <CompareView />;
  }
  if (params.alphaId) {
    return <DetailView alphaId={params.alphaId} />;
  }
  return <BrowseView />;
}

/* ---------- Browse view ---------- */

function BrowseView() {
  const [alphas, setAlphas] = useState<AlphaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [zooFilter, setZooFilter] = useState<string>("");
  const [themeFilter, setThemeFilter] = useState<string>("");
  const [universeFilter, setUniverseFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [total, setTotal] = useState<number>(0);
  // Alphas ticked for a head-to-head compare; handed to CompareView via the URL.
  const [selected, setSelected] = useState<Set<string>>(() => new Set());

  const toggleSelected = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const compareHref =
    selected.size >= 2
      ? `/alpha-zoo/compare?ids=${[...selected].map(encodeURIComponent).join(",")}`
      : "/alpha-zoo/compare";

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api
      .listAlphas({
        zoo: zooFilter || undefined,
        theme: themeFilter || undefined,
        universe: universeFilter || undefined,
        limit: 1000,
      })
      .then((res) => {
        if (!alive) return;
        setAlphas(res.alphas);
        setTotal(res.total);
        setVisibleCount(PAGE_SIZE);
      })
      .catch((err: unknown) => {
        if (!alive) return;
        const msg = err instanceof Error ? err.message : "Failed to load alphas";
        toast.error(msg);
        setAlphas([]);
        setTotal(0);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [zooFilter, themeFilter, universeFilter]);

  const themeOptions = useMemo(() => {
    const set = new Set<string>();
    for (const a of alphas) for (const t of a.theme || []) set.add(t);
    return Array.from(set).sort();
  }, [alphas]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return alphas;
    return alphas.filter(
      (a) =>
        a.id.toLowerCase().includes(q) ||
        (a.nickname || "").toLowerCase().includes(q),
    );
  }, [alphas, search]);

  const visible = filtered.slice(0, visibleCount);

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Hero */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-wide">
          <Layers className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.title")}
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          {loading
            ? i18n.t("alphaZoo.prebuiltAlphaLoading")
            : i18n.t("alphaZoo.prebuiltAlpha", { count: total })}
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl">
          {i18n.t("alphaZoo.browseDesc")}
        </p>
      </div>

      {/* Zoo cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {ZOO_CARDS.map((z) => {
          const active = zooFilter === z.id;
          return (
            <button
              key={z.id}
              type="button"
              onClick={() => setZooFilter(active ? "" : z.id)}
              className={cn(
                "text-left border rounded-xl p-4 space-y-2 transition bg-gradient-to-br",
                z.accent,
                "hover:border-primary/50",
                active && "border-primary ring-1 ring-primary/30",
              )}
            >
              <div className="flex items-center justify-between">
                <Library className="h-5 w-5 text-primary" aria-hidden="true" />
                <span className="text-xs font-mono text-muted-foreground">
                  {z.approxCount}
                </span>
              </div>
              <h3 className="font-semibold text-sm leading-tight">{i18n.t("alphaZoo.zooCardTitle." + z.id)}</h3>
              <p className="text-xs text-muted-foreground line-clamp-3">
                {i18n.t("alphaZoo.zooCardDesc." + z.id)}
              </p>
            </button>
          );
        })}
      </div>

      {/* Filter bar */}
      <div className="flex flex-col md:flex-row md:items-end gap-3 border rounded-xl p-4 bg-card">
        <div className="flex-1 min-w-0">
          <label htmlFor="alpha-search" className="text-xs text-muted-foreground block mb-1">
            {i18n.t("alphaZoo.search")}
          </label>
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground"
              aria-hidden="true"
            />
            <input
              id="alpha-search"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setVisibleCount(PAGE_SIZE);
              }}
              placeholder={i18n.t("alphaZoo.searchPlaceholder")}
              className="w-full pl-9 pr-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </div>
        <div className="md:w-40">
          <label htmlFor="alpha-zoo-filter" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.zoo")}</label>
          <select
            id="alpha-zoo-filter"
            value={zooFilter}
            onChange={(e) => setZooFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="">{i18n.t("alphaZoo.allZoos")}</option>
            {ZOO_CARDS.map((z) => (
              <option key={z.id} value={z.id}>
                {i18n.t("alphaZoo.zooCardTitle." + z.id)}
              </option>
            ))}
          </select>
        </div>
        <div className="md:w-40">
          <label htmlFor="alpha-theme-filter" className="text-xs text-muted-foreground block mb-1">
            {i18n.t("alphaZoo.theme")}
          </label>
          <select
            id="alpha-theme-filter"
            value={themeFilter}
            onChange={(e) => setThemeFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="">{i18n.t("alphaZoo.allThemes")}</option>
            {themeOptions.map((tname) => (
              <option key={tname} value={tname}>
                {i18n.t("alphaZoo.themes." + tname, { defaultValue: tname })}
              </option>
            ))}
          </select>
        </div>
        <div className="md:w-44">
          <label htmlFor="alpha-universe-filter" className="text-xs text-muted-foreground block mb-1">
            {i18n.t("alphaZoo.universe")}
          </label>
          <select
            id="alpha-universe-filter"
            value={universeFilter}
            onChange={(e) => setUniverseFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="">{i18n.t("alphaZoo.allUniverses")}</option>
            {UNIVERSE_OPTIONS.map((u) => (
              <option key={u.value} value={u.value}>
                {i18n.t("alphaZoo.universeOption." + u.value)}
              </option>
            ))}
          </select>
        </div>
        <Link
          to={compareHref}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium hover:bg-muted hover:text-foreground transition"
          title={i18n.t("alphaZoo.compareTooltip")}
        >
          <ArrowLeftRight className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.compare")}
          {selected.size >= 2 ? ` (${selected.size})` : ""}
        </Link>
        <Link
          to="/alpha-zoo/bench"
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition"
        >
          <Play className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.runBenchmark")}
        </Link>
      </div>

      {/* Table */}
      {/* TODO(v0.2): switch to react-window if alpha count exceeds 5000 */}
      <div className="border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" aria-label={i18n.t("alphaZoo.alphaCatalogue")}>
            <caption className="sr-only">{i18n.t("alphaZoo.alphaCatalogue")}</caption>
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="w-10 px-3 py-2.5">
                  <span className="sr-only">{i18n.t("alphaZoo.selectForCompare")}</span>
                </th>
                <th className="text-left px-4 py-2.5 text-muted-foreground">
                  {i18n.t("alphaZoo.id")}
                </th>
                <th className="text-left px-4 py-2.5 text-muted-foreground">
                  {i18n.t("alphaZoo.zoo")}
                </th>
                <th className="text-left px-4 py-2.5 text-muted-foreground">
                  {i18n.t("alphaZoo.theme")}
                </th>
                <th className="text-left px-4 py-2.5 text-muted-foreground hidden md:table-cell">
                  {i18n.t("alphaZoo.universe")}
                </th>
                <th className="text-right px-4 py-2.5 text-muted-foreground" title={i18n.t("alphaZoo.predictiveHalfLifeTitle")}>
                  {i18n.t("alphaZoo.decayDays")}
                </th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin inline mr-2" aria-hidden="true" />
                    {i18n.t("alphaZoo.loadingAlphas")}
                  </td>
                </tr>
              ) : visible.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    {i18n.t("alphaZoo.noAlphasMatch")}
                  </td>
                </tr>
              ) : (
                visible.map((a) => (
                  <tr
                    key={`${a.zoo}:${a.id}`}
                    className={cn(
                      "border-b last:border-0 hover:bg-muted/20",
                      selected.has(a.id) && "bg-primary/5",
                    )}
                  >
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selected.has(a.id)}
                        onChange={() => toggleSelected(a.id)}
                        aria-label={`Select ${a.id} for compare`}
                        className="h-4 w-4 rounded border-input accent-primary cursor-pointer"
                      />
                    </td>
                    <td className="px-4 py-2 font-mono text-xs">
                      <Link
                        to={`/alpha-zoo/${encodeURIComponent(a.id)}`}
                        className="text-primary hover:underline"
                      >
                        {a.id}
                      </Link>
                      {a.nickname && (
                        <span className="ml-2 text-muted-foreground font-sans">
                          {a.nickname}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-xs">{a.zoo}</td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">
                      {(a.theme || []).map((t) => i18n.t("alphaZoo.themes." + t, { defaultValue: t })).join(", ") || "—"}
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground hidden md:table-cell">
                      {(a.universe || []).map((u) => i18n.t("alphaZoo.universeOption." + u, { defaultValue: u })).join(", ") || "—"}
                    </td>
                    <td className="px-4 py-2 text-right font-mono tabular-nums text-xs">
                      {a.decay_horizon ?? "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && visible.length < filtered.length && (
          <div className="border-t p-3 flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {i18n.t("alphaZoo.showingOf", { visible: visible.length, total: filtered.length })}
            </span>
            <button
              type="button"
              onClick={() => setVisibleCount((c) => c + PAGE_SIZE)}
              className="px-3 py-1 rounded-md border hover:bg-muted hover:text-foreground transition"
            >
              {i18n.t("alphaZoo.loadMore")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Detail view ---------- */

interface DetailProps {
  alphaId: string;
}

function DetailView({ alphaId }: DetailProps) {
  const [detail, setDetail] = useState<AlphaDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .getAlpha(alphaId)
      .then((res) => {
        if (alive) setDetail(res);
      })
      .catch((err: unknown) => {
        if (!alive) return;
        const msg = err instanceof Error ? err.message : "Failed to load alpha";
        setError(msg);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [alphaId]);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin mr-2" aria-hidden="true" /> {i18n.t("alphaZoo.loadingAlpha", { id: alphaId })}
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="p-8 max-w-3xl mx-auto space-y-4">
        <Link to="/alpha-zoo" className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1">
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.backToAlphaZoo")}
        </Link>
        <div className="border rounded-xl p-6 bg-card">
          <h2 className="font-semibold text-sm mb-1 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-warning" aria-hidden="true" /> {i18n.t("alphaZoo.couldNotLoad")}
          </h2>
          <p className="text-sm text-muted-foreground">{error || i18n.t("alphaZoo.unknownError")}</p>
        </div>
      </div>
    );
  }

  const a = detail.alpha;
  const meta = a.meta || {};
  const formulaLatex = (meta["formula_latex"] as string | undefined) || "";
  const nickname = (meta["nickname"] as string | undefined) || "";
  const firstUniverse = ((meta["universe"] as string[] | undefined) || [])[0] || "";

  // Keep period in sync with the BenchView form default so the prefilled
  // form values match what users see if they click "Run bench" from here.
  const benchHref = firstUniverse
    ? `/alpha-zoo/bench?zoo=${encodeURIComponent(a.zoo)}&universe=${encodeURIComponent(firstUniverse)}&period=2020-2025`
    : `/alpha-zoo/bench?zoo=${encodeURIComponent(a.zoo)}&period=2020-2025`;

  return (
    <div className="p-4 md:p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <Link
          to="/alpha-zoo"
          className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.backToAlphaZoo")}
        </Link>
        <button
          type="button"
          onClick={() => navigate(benchHref)}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition"
        >
          <Play className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.runBenchmark")}
        </button>
      </div>

      {/* Title */}
      <div className="space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h1 className="font-mono text-xl md:text-2xl font-bold tracking-tight">
            {a.id}
          </h1>
          <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
            {a.zoo}
          </span>
        </div>
        {nickname && (
          <p className="text-sm text-muted-foreground">{nickname}</p>
        )}
      </div>

      {/* Formula */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">{i18n.t("alphaZoo.formula")}</h2>
        <pre className="border rounded-xl bg-muted/30 p-4 overflow-x-auto text-xs leading-relaxed">
          <code>{formulaLatex || i18n.t("alphaZoo.noFormula")}</code>
        </pre>
      </section>

      {/* Metadata */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">{i18n.t("alphaZoo.metadata")}</h2>
        <div className="border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <tbody>
              <MetaRow
                label={i18n.t("alphaZoo.theme")}
                value={
                  Array.isArray(meta.theme)
                    ? meta.theme.map((t: string) => i18n.t("alphaZoo.themes." + t, { defaultValue: t })).join(", ")
                    : typeof meta.theme === "string"
                    ? i18n.t("alphaZoo.themes." + meta.theme, { defaultValue: meta.theme })
                    : "—"
                }
              />
              <MetaRow
                label={i18n.t("alphaZoo.universe")}
                value={
                  Array.isArray(meta.universe)
                    ? meta.universe.map((u: string) => i18n.t("alphaZoo.universeOption." + u, { defaultValue: u })).join(", ")
                    : typeof meta.universe === "string"
                    ? i18n.t("alphaZoo.universeOption." + meta.universe, { defaultValue: meta.universe })
                    : "—"
                }
              />
              <MetaRow label={i18n.t("alphaZoo.frequency")} value={metaString(meta, "frequency")} />
              <MetaRow label={i18n.t("alphaZoo.decayHorizon")} value={metaString(meta, "decay_horizon")} />
              <MetaRow label={i18n.t("alphaZoo.minWarmupBars")} value={metaString(meta, "min_warmup_bars")} />
              <MetaRow label={i18n.t("alphaZoo.requiresSector")} value={metaString(meta, "requires_sector")} />
              <MetaRow label={i18n.t("alphaZoo.modulePath")} value={a.module_path || "—"} />
              <MetaRow label={i18n.t("alphaZoo.notes")} value={metaString(meta, "notes")} last />
            </tbody>
          </table>
        </div>
      </section>

      {/* Source code */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">{i18n.t("alphaZoo.sourceCode")}</h2>
        <details className="border rounded-xl bg-card group">
          <summary className="cursor-pointer px-4 py-3 text-sm font-medium hover:bg-muted/40 select-none">
            {i18n.t("alphaZoo.viewSource", { lines: (detail.source_code || "").split("\n").length })}
          </summary>
          <pre className="border-t bg-muted/30 p-4 overflow-x-auto text-xs leading-relaxed">
            <code>{detail.source_code || i18n.t("alphaZoo.noSource")}</code>
          </pre>
        </details>
      </section>
    </div>
  );
}

function MetaRow({ label, value, last }: { label: string; value: string; last?: boolean }) {
  return (
    <tr className={cn(!last && "border-b", "hover:bg-muted/20")}>
      <td className="px-4 py-2 text-xs text-muted-foreground w-1/3">{label}</td>
      <td className="px-4 py-2 text-xs font-mono break-all">{value}</td>
    </tr>
  );
}

/* ---------- Bench view ---------- */

type BenchStatus = "idle" | "submitting" | "streaming" | "done" | "error";

interface BenchProgress {
  n_done: number;
  n_total: number;
  current_alpha_id?: string;
}

function BenchView() {
  // Read prefill from query string (set by Detail "Run bench" button).
  const { search: locSearch } = useLocation();
  const initial = useMemo(() => {
    const q = new URLSearchParams(locSearch);
    return {
      zoo: q.get("zoo") || "alpha101",
      universe: q.get("universe") || "csi300",
      period: q.get("period") || "2020-2025",
      top: Number(q.get("top") || "20"),
    };
  }, [locSearch]);

  const [zoo, setZoo] = useState(initial.zoo);
  const [universe, setUniverse] = useState(initial.universe);
  const [period, setPeriod] = useState(initial.period);
  const [top, setTop] = useState<number>(initial.top);

  const [status, setStatus] = useState<BenchStatus>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<BenchProgress | null>(null);
  const [result, setResult] = useState<AlphaBenchResult | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);
  // Track terminal `done` so the synthetic EventSource `error` fired on
  // close doesn't surface as a spurious toast (race between done + error).
  const doneRef = useRef(false);

  useEffect(() => {
    return () => {
      sourceRef.current?.close();
      sourceRef.current = null;
    };
  }, []);

  const startBench = async (e: FormEvent) => {
    e.preventDefault();
    if (status === "submitting" || status === "streaming") return;
    setStatus("submitting");
    setProgress(null);
    setResult(null);
    setFormError(null);
    doneRef.current = false;
    sourceRef.current?.close();
    const safeTop = Number.isFinite(top) && top > 0 ? top : 20;
    try {
      const res = await api.createAlphaBench({
        zoo,
        universe,
        period,
        top: safeTop,
      });
      setJobId(res.job_id);
      attachStream(res.job_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to start bench";
      // BTC-USDT is single-asset — surface inline rather than as a toast,
      // because the form is the action context and the message includes a
      // concrete suggestion for the user's next step.
      if (msg.toLowerCase().includes("single-asset")) {
        setFormError(
          `${msg} Try \`sp500\` or \`csi300\` for a meaningful cross-sectional IC.`,
        );
      } else {
        toast.error(msg);
      }
      setStatus("error");
    }
  };

  const attachStream = (newJobId: string) => {
    setStatus("streaming");
    const url = api.alphaBenchStreamUrl(newJobId);
    const source = new EventSource(url);
    sourceRef.current = source;

    source.addEventListener("progress", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data) as BenchProgress;
        setProgress(data);
      } catch {
        /* ignore */
      }
    });

    source.addEventListener("result", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data) as AlphaBenchResult;
        setResult(data);
      } catch {
        /* ignore */
      }
    });

    source.addEventListener("done", () => {
      doneRef.current = true;
      setStatus("done");
      source.close();
      sourceRef.current = null;
    });

    source.addEventListener("error", (e) => {
      // EventSource raises a synthetic error on every disconnect, including
      // the normal close that follows our `done` event. The ref check is
      // synchronous (state updates from `done` would be batched and not
      // visible here yet), so it's the only reliable race guard.
      if (doneRef.current) {
        source.close();
        sourceRef.current = null;
        return;
      }
      let msg = "Bench stream error";
      try {
        const data = JSON.parse((e as MessageEvent).data || "{}");
        if (typeof data.message === "string") msg = data.message;
      } catch {
        /* network-level error, no payload */
      }
      toast.error(msg);
      setStatus("error");
      source.close();
      sourceRef.current = null;
    });
  };

  const busy = status === "submitting" || status === "streaming";

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-6">
      <Link
        to="/alpha-zoo"
        className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.backToAlphaZoo")}
      </Link>

      <div className="space-y-1">
        <div className="flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-wide">
          <Play className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.benchRunner")}
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          {i18n.t("alphaZoo.scoreZoo")}
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl">
          {i18n.t("alphaZoo.scoreDesc")}
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={startBench}
        className="border rounded-xl p-4 bg-card grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end"
      >
        <div>
          <label htmlFor="bench-zoo" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.zoo")}</label>
          <select
            id="bench-zoo"
            value={zoo}
            onChange={(e) => setZoo(e.target.value)}
            disabled={busy}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
          >
            {ZOO_CARDS.map((z) => (
              <option key={z.id} value={z.id}>
                {i18n.t("alphaZoo.zooCardTitle." + z.id)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="bench-universe" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.universe")}</label>
          <select
            id="bench-universe"
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
            disabled={busy}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
          >
            {UNIVERSE_OPTIONS.map((u) => (
              <option key={u.value} value={u.value}>
                {i18n.t("alphaZoo.universeOption." + u.value)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="bench-period" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.period")}</label>
          <input
            id="bench-period"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            disabled={busy}
            placeholder="2020-2025"
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
          />
        </div>
        <div>
          <label htmlFor="bench-top" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.top")}</label>
          <input
            id="bench-top"
            type="number"
            min={1}
            max={500}
            value={Number.isFinite(top) ? top : ""}
            onChange={(e) =>
              // Empty input → fall back to default; submit also clamps
              // to a safe value so NaN never reaches the API.
              setTop(e.target.value === "" ? 20 : Number(e.target.value))
            }
            disabled={busy}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
          />
        </div>
        <div className="flex flex-col gap-1">
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition disabled:opacity-50"
          >
            {busy ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> {i18n.t("alphaZoo.running")}
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.runBenchmark")}
              </>
            )}
          </button>
        </div>
        {formError && (
          <p
            className="sm:col-span-2 lg:col-span-5 text-xs text-red-600 dark:text-red-400"
            role="alert"
          >
            {formError}
          </p>
        )}
      </form>

      {/* Progress */}
      {(status === "submitting" || status === "streaming") && (
        <ProgressPanel jobId={jobId} progress={progress} />
      )}

      {/* Result */}
      {result && <ResultPanel result={result} />}
    </div>
  );
}

function ProgressPanel({
  jobId,
  progress,
}: {
  jobId: string | null;
  progress: BenchProgress | null;
}) {
  const pct = progress && progress.n_total > 0
    ? Math.min(100, Math.round((progress.n_done / progress.n_total) * 100))
    : 0;
  return (
    <div className="border rounded-xl p-4 bg-card space-y-3">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          {jobId ? `Job ${jobId.slice(0, 12)}…` : "Submitting…"}
        </span>
        {progress && (
          <span className="font-mono tabular-nums">
            {progress.n_done} / {progress.n_total}
          </span>
        )}
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      {progress?.current_alpha_id && (
        <p className="text-xs text-muted-foreground font-mono truncate">
          {i18n.t("alphaZoo.computing", { id: progress.current_alpha_id })}
        </p>
      )}
    </div>
  );
}

function ResultPanel({ result }: { result: AlphaBenchResult }) {
  const { dark } = useDarkMode();
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const theme = getChartTheme();
    const chart = echarts.init(chartRef.current);
    const themes = Object.keys(result.by_theme || {}).sort();
    const aliveSeries = themes.map((k) => result.by_theme[k].alive);
    const reversedSeries = themes.map((k) => result.by_theme[k].reversed);
    const deadSeries = themes.map((k) => result.by_theme[k].dead);

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      legend: {
        data: [i18n.t("alphaZoo.alive"), i18n.t("alphaZoo.reversed"), i18n.t("alphaZoo.dead")],
        textStyle: { color: theme.textColor, fontSize: 11 },
        right: 8,
        top: 4,
      },
      grid: { left: 8, right: 8, top: 32, bottom: 8, containLabel: true },
      xAxis: {
        type: "category",
        data: themes.map((t) => i18n.t("alphaZoo.themes." + t, { defaultValue: t })),
        axisLine: { lineStyle: { color: theme.axisColor } },
        axisLabel: { color: theme.textColor, fontSize: 10, rotate: themes.length > 6 ? 30 : 0 },
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: theme.gridColor } },
        axisLabel: { color: theme.textColor, fontSize: 10 },
      },
      series: [
        { name: i18n.t("alphaZoo.alive"), type: "bar", stack: "n", data: aliveSeries, itemStyle: { color: theme.upColor } },
        { name: i18n.t("alphaZoo.reversed"), type: "bar", stack: "n", data: reversedSeries, itemStyle: { color: theme.warningColor } },
        { name: i18n.t("alphaZoo.dead"), type: "bar", stack: "n", data: deadSeries, itemStyle: { color: theme.downColor } },
      ],
    });

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(chartRef.current);
    return () => {
      ro.disconnect();
      chart.dispose();
    };
  }, [result, dark]);

  const totals = [
    { label: i18n.t("alphaZoo.alive"), value: result.alive, icon: CheckCircle2, tone: "text-green-600 dark:text-green-400" },
    { label: i18n.t("alphaZoo.reversed"), value: result.reversed, icon: AlertTriangle, tone: "text-amber-600 dark:text-amber-400" },
    { label: i18n.t("alphaZoo.dead"), value: result.dead, icon: XCircle, tone: "text-red-600 dark:text-red-400" },
    { label: i18n.t("alphaZoo.skipped"), value: result.skipped ?? 0, icon: Loader2, tone: "text-muted-foreground" },
  ];

  return (
    <div className="space-y-4">
      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {totals.map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className="border rounded-xl p-4 bg-card flex items-center gap-3">
            <Icon className={cn("h-5 w-5 shrink-0", tone)} aria-hidden="true" />
            <div>
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-xl font-bold tabular-nums">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Top tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TopTable title={i18n.t("alphaZoo.topByIr")} rows={result.top5_by_ir || []} />
        <TopTable title={i18n.t("alphaZoo.mostReversed")} rows={(result.dead_examples || []).slice(0, 3)} />
      </div>

      {/* By-theme breakdown */}
      {result.by_theme && Object.keys(result.by_theme).length > 0 && (
        <div className="border rounded-xl p-4 bg-card">
          <h3 className="text-sm font-medium text-muted-foreground mb-2">
            {i18n.t("alphaZoo.byTheme")}
          </h3>
          <div ref={chartRef} style={{ height: 240 }} />
        </div>
      )}
    </div>
  );
}

function TopTable({ title, rows }: { title: string; rows: AlphaBenchTopRow[] }) {
  return (
    <div className="border rounded-xl overflow-hidden bg-card">
      <div className="px-4 py-2.5 border-b bg-muted/40">
        <h3 className="text-sm font-medium">{title}</h3>
      </div>
      {rows.length === 0 ? (
        <div className="px-4 py-6 text-xs text-muted-foreground text-center">
          {i18n.t("alphaZoo.noRows")}
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium">{i18n.t("alphaZoo.id")}</th>
              <th className="text-right px-4 py-2 text-xs text-muted-foreground font-medium">{i18n.t("alphaZoo.meanIc")}</th>
              <th className="text-right px-4 py-2 text-xs text-muted-foreground font-medium">{i18n.t("alphaZoo.ir")}</th>
              <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium">{i18n.t("alphaZoo.theme")}</th>
              <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium">{i18n.t("alphaZoo.category")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b last:border-0 hover:bg-muted/20">
                <td className="px-4 py-2">
                  <Link
                    to={`/alpha-zoo/${encodeURIComponent(r.id)}`}
                    className="text-primary hover:underline font-mono text-xs"
                  >
                    {r.id}
                  </Link>
                </td>
                <td className="px-4 py-2 text-right font-mono tabular-nums text-xs">{fmtNum(r.ic_mean)}</td>
                <td className="px-4 py-2 text-right font-mono tabular-nums text-xs">{fmtNum(r.ir)}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">
                  {(r.theme || []).map((t) => i18n.t("alphaZoo.themes." + t, { defaultValue: t })).join(", ") || "—"}
                </td>
                <td className="px-4 py-2 text-xs">
                  <CategoryBadge category={r.category} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

/**
 * Render the alpha bench category as a colored badge so users can see whether
 * a row is alive / reversed / dead at a glance. The "Most reversed" panel
 * mixes reversed + dead rows; the badge keeps them distinguishable.
 */
function CategoryBadge({ category }: { category: AlphaBenchTopRow["category"] }) {
  const tone =
    category === "alive"
      ? "bg-green-500/10 text-green-700 dark:text-green-300"
      : category === "reversed"
        ? "bg-amber-500/10 text-amber-700 dark:text-amber-300"
        : "bg-red-500/10 text-red-700 dark:text-red-300";
  const label =
    category === "alive"
      ? i18n.t("alphaZoo.alive")
      : category === "reversed"
        ? i18n.t("alphaZoo.reversed")
        : i18n.t("alphaZoo.dead");
  return (
    <span className={cn("inline-block px-2 py-0.5 rounded-full text-[10px] font-medium", tone)}>
      {label}
    </span>
  );
}

/* ---------- Compare view ---------- */

const SORT_OPTIONS = [
  { value: "ir", label: "IR (information ratio)" },
  { value: "ic_mean", label: "IC mean" },
  { value: "ic_positive_ratio", label: "IC > 0 ratio" },
  { value: "ic_count", label: "Sample count" },
];

/** Split a free-text id list on commas / whitespace; dedupe, preserve order. */
function parseAlphaIds(text: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of text.split(/[\s,]+/)) {
    const id = raw.trim();
    if (id && !seen.has(id)) {
      seen.add(id);
      out.push(id);
    }
  }
  return out;
}

/**
 * Head-to-head comparison of a hand-picked set of alphas.
 *
 * Mirrors {@link BenchView}'s raw-EventSource lifecycle (the shared `useSSE`
 * hook drops these event types). Ids are prefilled from `?ids=a,b,c` — set by
 * the BrowseView multi-select — and remain editable as free text.
 */
function CompareView() {
  const { search: locSearch } = useLocation();
  const initialIds = useMemo(() => {
    const q = new URLSearchParams(locSearch);
    return parseAlphaIds(q.get("ids") || "").join(", ");
  }, [locSearch]);

  const [idsText, setIdsText] = useState(initialIds);
  const [universe, setUniverse] = useState("csi300");
  const [period, setPeriod] = useState("2020-2025");
  const [sort, setSort] = useState("ir");

  const [status, setStatus] = useState<BenchStatus>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<BenchProgress | null>(null);
  const [result, setResult] = useState<AlphaCompareResult | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);
  const doneRef = useRef(false);

  const ids = useMemo(() => parseAlphaIds(idsText), [idsText]);

  useEffect(() => {
    return () => {
      sourceRef.current?.close();
      sourceRef.current = null;
    };
  }, []);

  const attachStream = (newJobId: string) => {
    setStatus("streaming");
    const source = new EventSource(api.alphaCompareStreamUrl(newJobId));
    sourceRef.current = source;

    source.addEventListener("progress", (e) => {
      try {
        setProgress(JSON.parse((e as MessageEvent).data) as BenchProgress);
      } catch {
        /* ignore */
      }
    });
    source.addEventListener("result", (e) => {
      try {
        setResult(JSON.parse((e as MessageEvent).data) as AlphaCompareResult);
      } catch {
        /* ignore */
      }
    });
    source.addEventListener("done", () => {
      doneRef.current = true;
      setStatus("done");
      source.close();
      sourceRef.current = null;
    });
    source.addEventListener("error", (e) => {
      // EventSource raises a synthetic error on the close that follows `done`;
      // the ref check (synchronous) is the only reliable race guard.
      if (doneRef.current) {
        source.close();
        sourceRef.current = null;
        return;
      }
      let msg = "Compare stream error";
      try {
        const data = JSON.parse((e as MessageEvent).data || "{}");
        if (typeof data.message === "string") msg = data.message;
      } catch {
        /* network-level error, no payload */
      }
      toast.error(msg);
      setStatus("error");
      source.close();
      sourceRef.current = null;
    });
  };

  const startCompare = async (e: FormEvent) => {
    e.preventDefault();
    if (status === "submitting" || status === "streaming") return;
    if (ids.length < 2) {
      setFormError("Enter at least 2 distinct alpha ids to compare.");
      return;
    }
    setStatus("submitting");
    setProgress(null);
    setResult(null);
    setFormError(null);
    doneRef.current = false;
    sourceRef.current?.close();
    try {
      const res = await api.createAlphaCompare({
        alpha_ids: ids,
        universe,
        period,
        sort,
      });
      setJobId(res.job_id);
      attachStream(res.job_id);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to start comparison";
      toast.error(msg);
      setStatus("error");
    }
  };

  const busy = status === "submitting" || status === "streaming";

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-6">
      <Link
        to="/alpha-zoo"
        className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.backToAlphaZoo")}
      </Link>

      <div className="space-y-1">
        <div className="flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-wide">
          <ArrowLeftRight className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.headToHeadCompare")}
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          {i18n.t("alphaZoo.compareAlphas")}
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl">
          {i18n.t("alphaZoo.compareDesc")}
        </p>
      </div>

      <form onSubmit={startCompare} className="border rounded-xl p-4 bg-card space-y-3">
        <div>
          <label htmlFor="compare-ids" className="text-xs text-muted-foreground block mb-1">
            {i18n.t("alphaZoo.alphaIds")}{ids.length > 0 ? ` (${ids.length} ${i18n.t("alphaZoo.selected")})` : ""}
          </label>
          <textarea
            id="compare-ids"
            value={idsText}
            onChange={(e) => setIdsText(e.target.value)}
            disabled={busy}
            rows={2}
            placeholder="alpha101_1, alpha101_2, gtja191_5"
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
          />
          <p className="text-[11px] text-muted-foreground mt-1">
            {i18n.t("alphaZoo.alphaIdsHint")}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label htmlFor="compare-universe" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.universe")}</label>
            <select
              id="compare-universe"
              value={universe}
              onChange={(e) => setUniverse(e.target.value)}
              disabled={busy}
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
            >
              {UNIVERSE_OPTIONS.map((u) => (
                <option key={u.value} value={u.value}>
                  {i18n.t("alphaZoo.universeOption." + u.value)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="compare-period" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.period")}</label>
            <input
              id="compare-period"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              disabled={busy}
              placeholder="2020-2025"
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
            />
          </div>
          <div>
            <label htmlFor="compare-sort" className="text-xs text-muted-foreground block mb-1">{i18n.t("alphaZoo.rankBy")}</label>
            <select
              id="compare-sort"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              disabled={busy}
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
            >
              {SORT_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {i18n.t("alphaZoo.sortOption." + (s.value === "ic_mean" ? "icMean" : s.value === "ic_positive_ratio" ? "icPositiveRatio" : s.value === "ic_count" ? "icCount" : s.value))}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={busy || ids.length < 2}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition disabled:opacity-50"
          >
            {busy ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> {i18n.t("alphaZoo.running")}
              </>
            ) : (
              <>
                <ArrowLeftRight className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.compare")}
              </>
            )}
          </button>
          {ids.length < 2 && (
            <span className="text-xs text-muted-foreground">{i18n.t("alphaZoo.pickAtLeast2")}</span>
          )}
        </div>

        {formError && (
          <p className="text-xs text-red-600 dark:text-red-400" role="alert">
            {formError}
          </p>
        )}
      </form>

      {(status === "submitting" || status === "streaming") && (
        <ProgressPanel jobId={jobId} progress={progress} />
      )}

      {result && <CompareResultPanel result={result} />}
    </div>
  );
}

function CompareResultPanel({ result }: { result: AlphaCompareResult }) {
  const deltaKey = `delta_${result.sort}_vs_best`;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        <span className="inline-flex items-center gap-1.5 font-medium text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> {i18n.t("alphaZoo.winner")}:{" "}
          <span className="font-mono">{result.winner}</span>
        </span>
        <span className="text-muted-foreground">
          {i18n.t("alphaZoo.comparedRankedBy", {
            count: result.n_compared,
            sort: result.sort,
            universe: result.universe,
            period: result.period,
          })}
        </span>
        {result.n_skipped > 0 && (
          <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" /> {i18n.t("alphaZoo.skippedCount", { count: result.n_skipped })}
          </span>
        )}
      </div>

      <div className="border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" aria-label={i18n.t("alphaZoo.alphaComparisonRanking")}>
            <thead>
              <tr className="border-b bg-muted/40 text-muted-foreground text-xs">
                <th className="text-right px-3 py-2">#</th>
                <th className="text-left px-3 py-2">{i18n.t("alphaZoo.alpha")}</th>
                <th className="text-right px-3 py-2 hidden sm:table-cell">{i18n.t("alphaZoo.zoo")}</th>
                <th className="text-right px-3 py-2">{i18n.t("alphaZoo.icMean")}</th>
                <th className="text-right px-3 py-2 hidden md:table-cell">{i18n.t("alphaZoo.icStd")}</th>
                <th className="text-right px-3 py-2">{i18n.t("alphaZoo.ir")}</th>
                <th className="text-right px-3 py-2 hidden md:table-cell" title={i18n.t("alphaZoo.icPositiveTitle")}>{i18n.t("alphaZoo.icPositive")}</th>
                <th className="text-right px-3 py-2 hidden lg:table-cell" title={i18n.t("alphaZoo.icSampleCount")}>{i18n.t("alphaZoo.sampleCount")}</th>
                <th className="text-right px-3 py-2" title={i18n.t("alphaZoo.gapTitle", { sort: result.sort })}>Δ {result.sort}</th>
              </tr>
            </thead>
            <tbody>
              {result.ranking.map((r) => (
                <tr
                  key={`${r.zoo}:${r.id}`}
                  className={cn(
                    "border-b last:border-0 hover:bg-muted/20",
                    r.rank === 1 && "bg-emerald-500/5",
                  )}
                >
                  <td className="px-3 py-2 text-right font-mono tabular-nums">{r.rank}</td>
                  <td className="px-3 py-2 font-mono text-xs">
                    <Link
                      to={`/alpha-zoo/${encodeURIComponent(r.id)}`}
                      className="text-primary hover:underline"
                    >
                      {r.id}
                    </Link>
                  </td>
                  <td className="px-3 py-2 text-xs text-muted-foreground hidden sm:table-cell">{r.zoo}</td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums">{fmtNum(r.ic_mean, 4)}</td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums hidden md:table-cell">{fmtNum(r.ic_std, 4)}</td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums">{fmtNum(r.ir, 3)}</td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums hidden md:table-cell">{fmtNum(r.ic_positive_ratio, 3)}</td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums hidden lg:table-cell">{r.ic_count}</td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums text-muted-foreground">
                    {r.rank === 1 ? "—" : fmtNum(Number(r[deltaKey]), 4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {result.skipped.length > 0 && (
        <p className="text-xs text-muted-foreground">
          <span className="font-medium">{i18n.t("alphaZoo.skippedPre")}</span>{" "}
          {result.skipped.map((s) => `${s.id} (${s.reason})`).join("; ")}
        </p>
      )}
    </div>
  );
}
