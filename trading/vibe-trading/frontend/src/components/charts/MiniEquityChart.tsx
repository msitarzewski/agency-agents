import { useEffect, useRef } from "react";
import { echarts } from "@/lib/echarts";
import { getChartTheme } from "@/lib/chart-theme";
import { useDarkMode } from "@/hooks/useDarkMode";

interface Props {
  data: Array<{ time: string; equity: number | string }>;
  height?: number;
}

export function MiniEquityChart({ data, height = 80 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const { dark } = useDarkMode();

  useEffect(() => {
    if (!ref.current || data.length < 2) return;
    const t = getChartTheme();
    const chart = echarts.init(ref.current);

    const values = data.map(d => Number(d.equity));
    const positive = values[values.length - 1] >= values[0];
    const color = positive ? t.upColor : t.downColor;

    chart.setOption({
      backgroundColor: "transparent",
      grid: { left: 0, right: 0, top: 0, bottom: 0 },
      xAxis: { type: "category", data: data.map(d => d.time), show: false },
      yAxis: { type: "value", show: false, scale: true },
      series: [{
        type: "line", data: values, symbol: "none", smooth: true,
        lineStyle: { color, width: 1.5 },
        areaStyle: {
          color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: color + "30" }, { offset: 1, color: color + "05" }],
          },
        },
      }],
    });

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(ref.current);
    return () => { ro.disconnect(); chart.dispose(); };
  }, [data, dark]);

  if (data.length < 2) return null;
  return <div ref={ref} style={{ height }} className="rounded-lg overflow-hidden" />;
}
