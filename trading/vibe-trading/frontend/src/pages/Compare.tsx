import i18n from '@/i18n';
import { useEffect, useRef, useState } from "react";
import { GitCompare, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { api, type RunListItem, type RunData, type EquityPoint } from "@/lib/api";
import { echarts, CHART_GROUP, connectCharts } from "@/lib/echarts";
import { getChartTheme } from "@/lib/chart-theme";
import { useDarkMode } from "@/hooks/useDarkMode";
import { SkeletonChart, SkeletonMetrics } from "@/components/common/Skeleton";

interface MetricDef {
  key: string;
  label: string;
  type: "pct" | "num" | "int" | "days";
  higherIsBetter: boolean;
}

function fmt(v: unknown, type: "pct" | "num" | "int" | "days" = "num"): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "\u2014";
  if (type === "pct") return (n * 100).toFixed(2) + "%";
  if (type === "int") return n.toFixed(0);
  if (type === "days") return n.toFixed(1);
  return n.toFixed(3);
}

function diffClass(a: unknown, b: unknown, higherIsBetter: boolean): string {
  const na = Number(a), nb = Number(b);
  if (!Number.isFinite(na) || !Number.isFinite(nb)) return "";
  const better = higherIsBetter ? nb > na : nb < na;
  const worse = higherIsBetter ? nb < na : nb > na;
  return better ? "text-green-600 dark:text-green-400" : worse ? "text-red-600 dark:text-red-400" : "";
}

function diffStr(a: unknown, b: unknown, type: "pct" | "num" | "int" | "days"): string {
  const na = Number(a), nb = Number(b);
  if (!Number.isFinite(na) || !Number.isFinite(nb)) return "\u2014";
  const d = nb - na;
  return (d > 0 ? "+" : "") + fmt(d, type);
}

function truncatePrompt(prompt: string | undefined, maxLen = 40): string {
  if (!prompt) return "";
  const trimmed = prompt.replace(/\n/g, " ").trim();
  return trimmed.length > maxLen ? trimmed.slice(0, maxLen) + "\u2026" : trimmed;
}

function runLabel(r: RunListItem): string {
  const summary = truncatePrompt(r.prompt);
  if (summary) return summary;
  return r.run_id;
}

const METRICS: MetricDef[] = [
  { key: "total_return",           label: i18n.t("compare.totalReturn"),         type: "pct", higherIsBetter: true },
  { key: "annualized_return",      label: i18n.t("compare.annualizedReturn"),    type: "pct", higherIsBetter: true },
  { key: "sharpe",                 label: i18n.t("compare.sharpeRatio"),         type: "num", higherIsBetter: true },
  { key: "calmar_ratio",           label: i18n.t("compare.calmarRatio"),         type: "num", higherIsBetter: true },
  { key: "sortino_ratio",          label: i18n.t("compare.sortinoRatio"),        type: "num", higherIsBetter: true },
  { key: "max_drawdown",           label: i18n.t("compare.maxDrawdown"),         type: "pct", higherIsBetter: false },
  { key: "volatility",             label: i18n.t("compare.volatility"),           type: "pct", higherIsBetter: false },
  { key: "win_rate",               label: i18n.t("compare.winRate"),             type: "pct", higherIsBetter: true },
  { key: "profit_factor",          label: i18n.t("compare.profitFactor"),        type: "num", higherIsBetter: true },
  { key: "avg_win",                label: i18n.t("compare.avgWin"),              type: "pct", higherIsBetter: true },
  { key: "avg_loss",               label: i18n.t("compare.avgLoss"),             type: "pct", higherIsBetter: false },
  { key: "trade_count",            label: i18n.t("compare.trades"),               type: "int", higherIsBetter: true },
  { key: "max_consecutive_losses", label: i18n.t("compare.maxConsecLosses"),   type: "int", higherIsBetter: false },
  { key: "exposure_time",          label: i18n.t("compare.exposureTime"),        type: "pct", higherIsBetter: true },
  { key: "avg_holding_period",     label: i18n.t("compare.avgHoldingPeriod"),   type: "days", higherIsBetter: false },
];

// Also accept backend aliases
const METRIC_ALIASES: Record<string, string> = {
  annual_return: "annualized_return",
  calmar: "calmar_ratio",
  sortino: "sortino_ratio",
  profit_loss_ratio: "profit_factor",
  max_consec_loss: "max_consecutive_losses",
  max_consecutive_loss: "max_consecutive_losses",
  avg_hold_days: "avg_holding_period",
  avg_holding_days: "avg_holding_period",
};

function resolveMetric(metrics: Record<string, number> | null, key: string): number | undefined {
  if (!metrics) return undefined;
  if (metrics[key] !== undefined) return metrics[key];
  // Check if any alias maps to this key
  for (const [alias, canonical] of Object.entries(METRIC_ALIASES)) {
    if (canonical === key && metrics[alias] !== undefined) return metrics[alias];
  }
  return undefined;
}

interface EquityChartOverlayProps {
  leftCurve: EquityPoint[];
  rightCurve: EquityPoint[];
  leftLabel: string;
  rightLabel: string;
}

function EquityChartOverlay({ leftCurve, rightCurve, leftLabel, rightLabel }: EquityChartOverlayProps) {
  const ref = useRef<HTMLDivElement>(null);
  const { dark } = useDarkMode();

  useEffect(() => {
    if (!ref.current) return;
    if (leftCurve.length === 0 && rightCurve.length === 0) return;

    const t = getChartTheme();
    const chart = echarts.init(ref.current);
    chart.group = CHART_GROUP;
    connectCharts();

    // Merge dates from both curves and sort
    const dateSet = new Set<string>();
    for (const p of leftCurve) dateSet.add(p.time);
    for (const p of rightCurve) dateSet.add(p.time);
    const dates = Array.from(dateSet).sort();

    // Build lookup maps
    const leftMap = new Map(leftCurve.map((p) => [p.time, Number(p.equity)]));
    const rightMap = new Map(rightCurve.map((p) => [p.time, Number(p.equity)]));

    const leftData = dates.map((d) => leftMap.get(d) ?? null);
    const rightData = dates.map((d) => rightMap.get(d) ?? null);

    const PRIMARY_COLOR = getComputedStyle(document.documentElement).getPropertyValue("--chart-compare-a").trim() || "#3b82f6";
    const SECONDARY_COLOR = getComputedStyle(document.documentElement).getPropertyValue("--chart-compare-b").trim() || "#f59e0b";

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
        backgroundColor: t.tooltipBg,
        borderColor: t.tooltipBorder,
        textStyle: { color: t.tooltipText, fontSize: 11 },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        formatter: (params: any) => {
          if (!Array.isArray(params) || !params.length) return "";
          let html = `<b>${params[0].axisValue}</b>`;
          for (const p of params) {
            if (p.value == null) continue;
            html += `<br/>${p.marker} ${p.seriesName}: <b>${Number(p.value).toLocaleString()}</b>`;
          }
          return html;
        },
      },
      legend: {
        data: [leftLabel, rightLabel],
        textStyle: { color: t.textColor, fontSize: 11 },
        right: 8,
        top: 4,
      },
      grid: { left: 8, right: 8, top: 36, bottom: 40, containLabel: true },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: t.axisColor } },
        axisLabel: { color: t.textColor, fontSize: 10 },
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: t.gridColor } },
        axisLabel: { color: t.textColor, fontSize: 10 },
      },
      dataZoom: [{ type: "inside" }, { type: "slider", height: 20, bottom: 4 }],
      series: [
        {
          name: leftLabel,
          type: "line",
          data: leftData,
          smooth: false,
          symbol: "none",
          lineStyle: { color: PRIMARY_COLOR, width: 2 },
          connectNulls: true,
        },
        {
          name: rightLabel,
          type: "line",
          data: rightData,
          smooth: false,
          symbol: "none",
          lineStyle: { color: SECONDARY_COLOR, width: 2 },
          connectNulls: true,
        },
      ],
    });

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(ref.current!);
    return () => { ro.disconnect(); chart.dispose(); };
  }, [leftCurve, rightCurve, leftLabel, rightLabel, dark]);

  if (leftCurve.length === 0 && rightCurve.length === 0) return null;

  return <div ref={ref} style={{ height: 320 }} />;
}

export function Compare() {
  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [leftId, setLeftId] = useState("");
  const [rightId, setRightId] = useState("");
  const [leftData, setLeftData] = useState<Record<string, number> | null>(null);
  const [rightData, setRightData] = useState<Record<string, number> | null>(null);
  const [leftCurve, setLeftCurve] = useState<EquityPoint[]>([]);
  const [rightCurve, setRightCurve] = useState<EquityPoint[]>([]);
  const [leftLoading, setLeftLoading] = useState(false);
  const [rightLoading, setRightLoading] = useState(false);

  useEffect(() => {
    api.listRuns().then((items) => {
      setRuns(Array.isArray(items) ? items : []);
      if (items.length >= 2) { setLeftId(items[1].run_id); setRightId(items[0].run_id); }
      else if (items.length === 1) { setLeftId(items[0].run_id); }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (leftId) {
      setLeftLoading(true);
      api.getRun(leftId).then((d: RunData) => {
        setLeftData(d.metrics || null);
        setLeftCurve(d.equity_curve || []);
      }).catch(() => { setLeftData(null); setLeftCurve([]); })
        .finally(() => setLeftLoading(false));
    } else {
      setLeftData(null);
      setLeftCurve([]);
    }
  }, [leftId]);

  useEffect(() => {
    if (rightId) {
      setRightLoading(true);
      api.getRun(rightId).then((d: RunData) => {
        setRightData(d.metrics || null);
        setRightCurve(d.equity_curve || []);
      }).catch(() => { setRightData(null); setRightCurve([]); })
        .finally(() => setRightLoading(false));
    } else {
      setRightData(null);
      setRightCurve([]);
    }
  }, [rightId]);

  const leftRun = runs.find((r) => r.run_id === leftId);
  const rightRun = runs.find((r) => r.run_id === rightId);
  const loading = leftLoading || rightLoading;
  const hasData = Boolean(leftData || rightData);

  return (
    <div className="p-8 max-w-4xl space-y-6">
      <h1 className="text-xl font-bold flex items-center gap-2">
        <GitCompare className="h-5 w-5" /> Strategy Comparison
      </h1>

      {/* Selectors */}
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <label className="text-xs text-muted-foreground block mb-1">{i18n.t("compare.baseline")}</label>
          <select value={leftId} onChange={(e) => setLeftId(e.target.value)} className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" title={leftRun?.prompt || leftId}>
            <option value="">{i18n.t("compare.select")}</option>
            {runs.map((r) => <option key={r.run_id} value={r.run_id}>{runLabel(r)} ({r.status})</option>)}
          </select>
        </div>
        <ArrowRight className="h-5 w-5 text-muted-foreground mb-2 shrink-0" />
        <div className="flex-1">
          <label className="text-xs text-muted-foreground block mb-1">{i18n.t("compare.compare")}</label>
          <select value={rightId} onChange={(e) => setRightId(e.target.value)} className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" title={rightRun?.prompt || rightId}>
            <option value="">{i18n.t("compare.select")}</option>
            {runs.map((r) => <option key={r.run_id} value={r.run_id}>{runLabel(r)} ({r.status})</option>)}
          </select>
        </div>
      </div>

      {/* Loading state — show skeletons while a selected run's data is in flight */}
      {loading && !hasData && (
        <div className="space-y-6">
          <div className="border rounded-xl p-4">
            <h2 className="text-sm font-medium text-muted-foreground mb-2">{i18n.t("compare.equityDrawdown")}</h2>
            <SkeletonChart height={320} />
          </div>
          <div className="border rounded-xl overflow-hidden">
            <SkeletonMetrics />
          </div>
        </div>
      )}

      {/* Equity curve overlay */}
      {(leftCurve.length > 0 || rightCurve.length > 0) && (
        <div className="border rounded-xl p-4">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">{i18n.t("compare.equityDrawdown")}</h2>
          <EquityChartOverlay
            leftCurve={leftCurve}
            rightCurve={rightCurve}
            leftLabel={leftRun ? truncatePrompt(leftRun.prompt, 20) || "Baseline" : "Baseline"}
            rightLabel={rightRun ? truncatePrompt(rightRun.prompt, 20) || "Compare" : "Compare"}
          />
        </div>
      )}

      {/* Metrics table */}
      {(leftData || rightData) && (
        <div className="border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="text-left px-4 py-2.5 text-muted-foreground font-medium">{i18n.t("compare.metric")}</th>
                <th className="text-right px-4 py-2.5 text-muted-foreground font-medium">{i18n.t("compare.baselineCol")}</th>
                <th className="text-right px-4 py-2.5 text-muted-foreground font-medium">{i18n.t("compare.compareCol")}</th>
                <th className="text-right px-4 py-2.5 text-muted-foreground font-medium">{i18n.t("compare.delta")}</th>
              </tr>
            </thead>
            <tbody>
              {METRICS.map(({ key, label, type, higherIsBetter }) => {
                const lv = resolveMetric(leftData, key);
                const rv = resolveMetric(rightData, key);
                return (
                  <tr key={key} className="border-b last:border-0 hover:bg-muted/20">
                    <td className="px-4 py-2.5 font-medium">{label}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums">{fmt(lv, type)}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums">{fmt(rv, type)}</td>
                    <td className={cn("px-4 py-2.5 text-right font-mono tabular-nums font-semibold", diffClass(lv, rv, higherIsBetter))}>{diffStr(lv, rv, type)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!hasData && !loading && (
        <div className="text-center py-16 text-muted-foreground">
          <GitCompare className="h-12 w-12 mx-auto mb-3 opacity-20" />
          <p className="text-sm">{i18n.t("compare.selectTwoRuns")}</p>
        </div>
      )}
    </div>
  );
}
