import { isReportWorthyRun } from "../runReports";
import { makeRunData } from "@/tests/helpers/factories";

describe("isReportWorthyRun", () => {
  it("returns false for null/undefined", () => {
    expect(isReportWorthyRun(null)).toBe(false);
    expect(isReportWorthyRun(undefined)).toBe(false);
  });

  it("returns false for empty run with no data", () => {
    expect(isReportWorthyRun(makeRunData())).toBe(false);
  });

  it("returns true when metrics has keys", () => {
    expect(
      isReportWorthyRun(makeRunData({ metrics: { total_return: 0.1, final_value: 10000 } })),
    ).toBe(true);
  });

  it("returns true when run_card has keys", () => {
    expect(
      isReportWorthyRun(makeRunData({ run_card: { schema_version: "1.0" } })),
    ).toBe(true);
  });

  it("returns true when equity_curve is non-empty", () => {
    expect(
      isReportWorthyRun(makeRunData({ equity_curve: [{ time: "2024-01-01", equity: 10000 }] })),
    ).toBe(true);
  });

  it("returns true when trade_log is non-empty", () => {
    expect(
      isReportWorthyRun(makeRunData({ trade_log: [{ date: "2024-01-01", action: "BUY" }] })),
    ).toBe(true);
  });

  it("returns true when trade_markers is non-empty", () => {
    expect(
      isReportWorthyRun(makeRunData({ trade_markers: [{ time: "2024-01-01", side: "buy", price: 100 }] })),
    ).toBe(true);
  });

  it("returns true when validation has keys", () => {
    expect(
      isReportWorthyRun(makeRunData({ validation: { passed: true } })),
    ).toBe(true);
  });

  it("returns true when price_series has non-empty array", () => {
    expect(
      isReportWorthyRun(
        makeRunData({
          price_series: {
            AAPL: [{ time: "2024-01-01", open: 100, high: 105, low: 99, close: 103, volume: 1000 }],
          },
        }),
      ),
    ).toBe(true);
  });

  it("returns false when price_series values are all empty arrays", () => {
    expect(
      isReportWorthyRun(makeRunData({ price_series: { AAPL: [] } })),
    ).toBe(false);
  });

  it("returns true when artifacts contain matching filenames", () => {
    expect(
      isReportWorthyRun(makeRunData({ artifacts: [{ name: "metrics.json", path: "/tmp/metrics.json" }] })),
    ).toBe(true);
    expect(
      isReportWorthyRun(makeRunData({ artifacts: [{ name: "trades.csv", path: "/tmp/t.csv" }] })),
    ).toBe(true);
    expect(
      isReportWorthyRun(makeRunData({ artifacts: [{ name: "strategy.pine", path: "/tmp/s.pine" }] })),
    ).toBe(true);
  });

  it("returns false for artifacts with non-matching names", () => {
    expect(
      isReportWorthyRun(makeRunData({ artifacts: [{ name: "readme.txt", path: "/tmp/r.txt" }] })),
    ).toBe(false);
  });

  it("handles empty artifacts array", () => {
    expect(isReportWorthyRun(makeRunData({ artifacts: [] }))).toBe(false);
  });
});
