import { localizeToolName, TOOL_LABELS } from "../tools";

describe("TOOL_LABELS", () => {
  it("maps known tool names to user-facing labels", () => {
    expect(TOOL_LABELS["run_backtest"]).toBe("Run backtest");
    expect(TOOL_LABELS["write_file"]).toBe("Generate code");
    expect(TOOL_LABELS["bash"]).toBe("Run command");
    expect(TOOL_LABELS["compact"]).toBe("Summarize conversation");
  });

  it("contains all trading connector tools", () => {
    const tradingKeys = Object.keys(TOOL_LABELS).filter((k) => k.startsWith("trading_"));
    expect(tradingKeys.length).toBeGreaterThanOrEqual(6);
  });
});

describe("localizeToolName", () => {
  it("returns label for known tools", () => {
    expect(localizeToolName("run_backtest")).toBe("Run backtest");
  });

  it("returns fallback for unknown tools when fallback provided", () => {
    expect(localizeToolName("unknown_tool", "My Fallback")).toBe("My Fallback");
  });

  it("returns raw tool name for unknown tools with no fallback", () => {
    expect(localizeToolName("some_new_tool")).toBe("some_new_tool");
  });

  it("prefers TOOL_LABELS over fallback", () => {
    expect(localizeToolName("bash", "ignored")).toBe("Run command");
  });
});
