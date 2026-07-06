import { useEffect, useRef } from "react";
import i18n from "@/i18n";
import type { EquityPoint } from "@/lib/api";
import { getChartTheme } from "@/lib/chart-theme";
import { abbreviateNum } from "@/lib/formatters";
import { echarts, CHART_GROUP, connectCharts } from "@/lib/echarts";
import { useDarkMode } from "@/hooks/useDarkMode";

interface Props {
  data: EquityPoint[];
  height?: number;
}

export function EquityChart({ data, height = 300 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const { dark } = useDarkMode();

  useEffect(() => {
    if (!ref.current || data.length === 0) return;
    const t = getChartTheme();
    const chart = echarts.init(ref.current);
    chart.group = CHART_GROUP;
    connectCharts();

    const dates = data.map((d) => d.time);
    const equity = data.map((d) => Number(d.equity));
    const drawdown = data.map((d) => (Number(d.drawdown) * 100).toFixed(2));
    const minDD = Math.min(...drawdown.map(Number));

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
            const val = p.seriesName === "Drawdown%"
              ? `${p.value}%`
              : Number(p.value).toLocaleString();
            html += `<br/>${p.marker} ${p.seriesName}: <b>${val}</b>`;
          }
          return html;
        },
      },
      toolbox: {
        feature: {
          saveAsImage: { title: "Save" },
          restore: { title: "Reset" },
        },
        right: 8, top: 0,
        iconStyle: { borderColor: t.textColor },
      },
      legend: { data: ["Equity", "Drawdown%"], textStyle: { color: t.textColor, fontSize: 11 }, right: 60, top: 4 },
      grid: [
        { left: 8, right: 8, top: 36, height: "56%", containLabel: true },
        { left: 8, right: 8, top: "68%", height: "20%", containLabel: true },
      ],
      xAxis: [
        { type: "category", data: dates, gridIndex: 0, axisLine: { lineStyle: { color: t.axisColor } }, axisLabel: { color: t.textColor, fontSize: 10 } },
        { type: "category", data: dates, gridIndex: 1, axisLine: { lineStyle: { color: t.axisColor } }, axisLabel: { show: false } },
      ],
      yAxis: [
        {
          type: "value", gridIndex: 0,
          splitLine: { lineStyle: { color: t.gridColor } },
          axisLabel: { color: t.textColor, fontSize: 10, formatter: (v: number) => abbreviateNum(v) },
        },
        {
          type: "value", gridIndex: 1,
          splitLine: { lineStyle: { color: t.gridColor } },
          axisLabel: { color: t.textColor, fontSize: 10, formatter: "{value}%" },
        },
      ],
      dataZoom: [{ type: "inside", xAxisIndex: [0, 1] }],
      series: [
        {
          name: "Equity", type: "line", xAxisIndex: 0, yAxisIndex: 0,
          data: equity, smooth: false, symbol: "none",
          lineStyle: { color: t.infoColor, width: 2 },
          areaStyle: {
            color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: t.infoColor + "40" }, { offset: 1, color: t.infoColor + "00" }] },
          },
        },
        {
          name: "Drawdown%", type: "line", xAxisIndex: 1, yAxisIndex: 1,
          data: drawdown, smooth: false, symbol: "none",
          lineStyle: { color: t.downColor, width: 1 },
          areaStyle: { color: t.downColor + "25" },
          markLine: {
            silent: true, symbol: "none",
            data: [{ yAxis: minDD, label: { formatter: `Max DD: ${minDD}%`, position: "insideEndTop", fontSize: 10, color: t.downColor } }],
            lineStyle: { color: t.downColor, type: "dashed", width: 1 },
          },
        },
      ],
    });

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(ref.current!);
    return () => { ro.disconnect(); chart.dispose(); };
  }, [data, dark]);

  if (data.length === 0) {
    return <div className="text-muted-foreground text-sm p-4">{i18n.t("charts.noEquityData")}</div>;
  }
  return <div ref={ref} style={{ height }} />;
}
