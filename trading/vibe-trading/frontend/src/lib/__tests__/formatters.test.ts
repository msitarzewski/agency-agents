import {
  getMetricLabel,
  formatMetricVal,
  metricSentiment,
  formatTimestamp,
  abbreviateNum,
  DISPLAY_ORDER,
  METRIC_LABELS,
} from "../formatters";

describe("getMetricLabel", () => {
  it("returns human label for known keys", () => {
    expect(getMetricLabel("sharpe")).toBe("Sharpe");
    expect(getMetricLabel("max_drawdown")).toBe("Max DD");
  });

  it("returns raw key for unknown keys", () => {
    expect(getMetricLabel("custom_metric")).toBe("custom_metric");
  });
});

describe("formatMetricVal", () => {
  // Percentage keys
  it("formats percentage keys with sign and %", () => {
    expect(formatMetricVal("total_return", 0.1234)).toBe("+12.34%");
    expect(formatMetricVal("annual_return", -0.05)).toBe("-5.00%");
    expect(formatMetricVal("win_rate", 0.5)).toBe("+50.00%");
    expect(formatMetricVal("max_drawdown", -0.15)).toBe("-15.00%");
  });

  it("formats zero percentage without sign", () => {
    // v > 0 is false when v === 0, so sign is ""
    expect(formatMetricVal("total_return", 0)).toBe("0.00%");
  });

  // Ratio keys
  it("formats ratio keys with sign", () => {
    expect(formatMetricVal("sharpe", 1.5)).toBe("+1.50");
    expect(formatMetricVal("sortino", -0.3)).toBe("-0.30");
  });

  // Integer keys
  it("formats integer keys as rounded whole numbers", () => {
    expect(formatMetricVal("trade_count", 42.7)).toBe("43");
    expect(formatMetricVal("max_consecutive_loss", 3.2)).toBe("3");
  });

  // Special keys
  it("formats final_value with locale grouping", () => {
    const result = formatMetricVal("final_value", 1234567);
    expect(result).toMatch(/1.*234.*567|1,234,567/);
  });

  it("formats avg_holding_days with one decimal", () => {
    expect(formatMetricVal("avg_holding_days", 3.456)).toBe("3.5");
  });

  // Fallback
  it("falls back to 4 decimal places for unknown keys", () => {
    expect(formatMetricVal("unknown_key", 1.23456789)).toBe("1.2346");
  });
});

describe("metricSentiment", () => {
  it("returns neutral for neutral keys regardless of value", () => {
    expect(metricSentiment("trade_count", 100)).toBe("neutral");
    expect(metricSentiment("avg_holding_days", 0)).toBe("neutral");
    expect(metricSentiment("final_value", -999)).toBe("neutral");
  });

  // max_drawdown thresholds
  it("max_drawdown: > -0.05 is positive", () => {
    expect(metricSentiment("max_drawdown", -0.01)).toBe("positive");
  });
  it("max_drawdown: -0.05 to -0.2 is neutral", () => {
    expect(metricSentiment("max_drawdown", -0.1)).toBe("neutral");
  });
  it("max_drawdown: <= -0.2 is negative", () => {
    expect(metricSentiment("max_drawdown", -0.25)).toBe("negative");
  });

  // win_rate thresholds
  it("win_rate: >= 0.5 is positive", () => {
    expect(metricSentiment("win_rate", 0.6)).toBe("positive");
  });
  it("win_rate: 0.35-0.5 is neutral", () => {
    expect(metricSentiment("win_rate", 0.4)).toBe("neutral");
  });
  it("win_rate: < 0.35 is negative", () => {
    expect(metricSentiment("win_rate", 0.2)).toBe("negative");
  });

  // sharpe/calmar/sortino thresholds
  it("sharpe: >= 1.0 positive, >= 0.3 neutral, < 0.3 negative", () => {
    expect(metricSentiment("sharpe", 1.5)).toBe("positive");
    expect(metricSentiment("sharpe", 0.5)).toBe("neutral");
    expect(metricSentiment("sharpe", 0.1)).toBe("negative");
  });

  // information_ratio
  it("information_ratio: >= 0.5 positive, >= 0 neutral, < 0 negative", () => {
    expect(metricSentiment("information_ratio", 0.6)).toBe("positive");
    expect(metricSentiment("information_ratio", 0.2)).toBe("neutral");
    expect(metricSentiment("information_ratio", -0.1)).toBe("negative");
  });

  // max_consecutive_loss
  it("max_consecutive_loss: <= 3 positive, <= 6 neutral, > 6 negative", () => {
    expect(metricSentiment("max_consecutive_loss", 2)).toBe("positive");
    expect(metricSentiment("max_consecutive_loss", 5)).toBe("neutral");
    expect(metricSentiment("max_consecutive_loss", 8)).toBe("negative");
  });

  // Generic fallback
  it("generic: positive > 0, neutral === 0, negative < 0", () => {
    expect(metricSentiment("total_return", 0.1)).toBe("positive");
    expect(metricSentiment("total_return", 0)).toBe("neutral");
    expect(metricSentiment("total_return", -0.1)).toBe("negative");
  });
});

describe("formatTimestamp", () => {
  it("formats timestamp as HH:MM with zero-padding", () => {
    const d = new Date(2024, 0, 1, 9, 5);
    expect(formatTimestamp(d.getTime())).toBe("09:05");
  });

  it("handles midnight", () => {
    const d = new Date(2024, 0, 1, 0, 0);
    expect(formatTimestamp(d.getTime())).toBe("00:00");
  });
});

describe("abbreviateNum", () => {
  it("abbreviates billions", () => {
    expect(abbreviateNum(1_500_000_000)).toBe("1.5B");
  });
  it("abbreviates millions", () => {
    expect(abbreviateNum(2_300_000)).toBe("2.3M");
  });
  it("abbreviates thousands", () => {
    expect(abbreviateNum(15_000)).toBe("15K");
  });
  it("returns locale string for small numbers", () => {
    expect(abbreviateNum(999)).toBe("999");
  });
  it("handles negative values", () => {
    expect(abbreviateNum(-2_500_000)).toBe("-2.5M");
  });
});

describe("DISPLAY_ORDER", () => {
  it("contains all keys from METRIC_LABELS", () => {
    const labelKeys = Object.keys(METRIC_LABELS);
    for (const key of labelKeys) {
      expect(DISPLAY_ORDER).toContain(key);
    }
  });
});
