import { useTranslation } from 'react-i18next';
import { memo, useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { BarChart3, Code2, FileText, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { AgentAvatar } from "./AgentAvatar";
import { MetricsCard } from "./MetricsCard";
import { MiniEquityChart } from "@/components/charts/MiniEquityChart";
import { PineScriptViewer } from "./PineScriptViewer";
import type { AgentMessage } from "@/types/agent";

interface Props {
  msg: AgentMessage;
}

export const RunCompleteCard = memo(function RunCompleteCard({ msg }: Props) {
  const { t } = useTranslation();
  const [curve, setCurve] = useState(msg.equityCurve);
  const [pineCode, setPineCode] = useState<string | null>(null);
  const [pineLoading, setPineLoading] = useState(false);
  const [showPine, setShowPine] = useState(false);
  const [pineChecked, setPineChecked] = useState(false);
  const [pineExists, setPineExists] = useState(false);

  useEffect(() => {
    if (!curve && msg.runId) {
      api.getRun(msg.runId).then(r => {
        if (r.equity_curve) setCurve(r.equity_curve.map(e => ({ time: e.time, equity: e.equity })));
      }).catch(() => {});
    }
  }, [msg.runId, curve]);

  // Check if Pine Script exists for this run (skip for shadow-only cards with no runId)
  useEffect(() => {
    if (!msg.runId) {
      setPineChecked(true);
      return;
    }
    if (!pineChecked) {
      api.getRunPine(msg.runId).then(r => {
        setPineChecked(true);
        if (r.exists && r.content) {
          setPineExists(true);
          setPineCode(r.content);
        }
      }).catch(() => { setPineChecked(true); });
    }
  }, [msg.runId, pineChecked]);

  const handlePineClick = useCallback(async () => {
    if (pineCode) {
      setShowPine(true);
      return;
    }
    if (!msg.runId) return;
    setPineLoading(true);
    try {
      const r = await api.getRunPine(msg.runId);
      if (r.exists && r.content) {
        setPineCode(r.content);
        setPineExists(true);
        setShowPine(true);
      }
    } catch { /* ignore */ }
    finally { setPineLoading(false); }
  }, [pineCode, msg.runId]);

  return (
    <div className="flex gap-3">
      <AgentAvatar />
      <div className="flex-1 min-w-0 space-y-2">
        {msg.metrics && Object.keys(msg.metrics).length > 0 && (
          <MetricsCard metrics={msg.metrics} compact />
        )}
        {curve && curve.length > 1 && (
          <MiniEquityChart data={curve} height={80} />
        )}
        <div className="flex items-center gap-3 flex-wrap">
          {msg.runId && (
            <Link
              to={`/runs/${msg.runId}`}
              className="text-sm text-primary hover:underline inline-flex items-center gap-1.5 font-medium"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              {t("runComplete.fullReport")}
            </Link>
          )}
          {pineExists && (
            <button
              onClick={handlePineClick}
              disabled={pineLoading}
              className="text-sm text-emerald-600 dark:text-emerald-400 hover:underline inline-flex items-center gap-1.5 font-medium disabled:opacity-50"
            >
              {pineLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Code2 className="h-3.5 w-3.5" />}
              Pine Script
            </button>
          )}
          {msg.shadowId && (
            <a
              href={`/shadow-reports/${encodeURIComponent(msg.shadowId)}?format=html`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-teal-600 dark:text-teal-400 hover:underline inline-flex items-center gap-1.5 font-medium"
            >
              <FileText className="h-3.5 w-3.5" />
              Shadow Report
            </a>
          )}
        </div>
        {showPine && pineCode && (
          <PineScriptViewer code={pineCode} onClose={() => setShowPine(false)} />
        )}
      </div>
    </div>
  );
});
