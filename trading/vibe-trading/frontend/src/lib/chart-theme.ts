function css(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function hslToHex(hsl: string): string {
  if (!hsl) return "";
  const [h, s, l] = hsl.split(/\s+/).map(parseFloat);
  if (isNaN(h)) return "";
  const a = (s / 100) * Math.min(l / 100, 1 - l / 100);
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const color = l / 100 - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

function isChinese(): boolean {
  return (document.documentElement.lang || navigator.language || "").startsWith("zh");
}

let _cache: ReturnType<typeof buildTheme> | null = null;
let _cacheKey = "";

function buildTheme() {
  const cn = isChinese();
  const isDark = document.documentElement.classList.contains("dark");

  const successHex = hslToHex(css("--success")) || "#22c55e";
  const dangerHex = hslToHex(css("--danger")) || "#ef4444";
  const infoHex = hslToHex(css("--info")) || "#3b82f6";
  const warningHex = hslToHex(css("--warning")) || "#f59e0b";
  const gridHex = hslToHex(css("--chart-grid")) || (isDark ? "#1e2433" : "#e5e7eb");
  const textHex = hslToHex(css("--chart-text")) || "#6b7280";
  const axisHex = hslToHex(css("--chart-axis")) || "#374151";

  // Locale-aware candlestick colors: China = red up / green down
  const upHex = cn ? dangerHex : successHex;
  const downHex = cn ? successHex : dangerHex;

  return {
    gridColor: gridHex,
    textColor: textHex,
    axisColor: axisHex,
    upColor: upHex,
    downColor: downHex,
    maColors: [warningHex, "#8b5cf6", infoHex],
    bollColor: "rgba(99,102,241,0.5)",
    volumeUp: upHex + "66",
    volumeDown: downHex + "66",
    infoColor: infoHex,
    warningColor: warningHex,
    tooltipBg: isDark ? "rgba(10,14,22,0.92)" : "rgba(255,255,255,0.96)",
    tooltipBorder: isDark ? "#1e2433" : "#e5e7eb",
    tooltipText: isDark ? "#d1d5db" : "#374151",
  };
}

export function getChartTheme() {
  const key = `${document.documentElement.className}|${document.documentElement.lang || navigator.language}`;
  if (_cache && _cacheKey === key) return _cache;
  _cache = buildTheme();
  _cacheKey = key;
  return _cache;
}
