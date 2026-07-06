import type { AgentMessage, ToolCallEntry } from "@/types/agent";

let _seq = 0;

export function makeMessage(overrides: Partial<AgentMessage> = {}): AgentMessage {
  return {
    id: `msg-${++_seq}`,
    type: "answer",
    content: "test content",
    timestamp: Date.now(),
    ...overrides,
  };
}

export function makeToolCall(overrides: Partial<ToolCallEntry> = {}): ToolCallEntry {
  return {
    id: `tc-${++_seq}`,
    tool: "bash",
    arguments: {},
    status: "running",
    timestamp: Date.now(),
    ...overrides,
  };
}

/** Minimal RunData shape for isReportWorthyRun tests */
type ReportWorthyInput = Parameters<typeof import("@/lib/runReports").isReportWorthyRun>[0];

export function makeRunData<T extends object = object>(overrides: T = {} as T): ReportWorthyInput {
  return {
    status: "done",
    run_id: `run-${++_seq}`,
    ...overrides,
  } as ReportWorthyInput;
}

/** Reset factory counters between test files */
export function resetFactories() {
  _seq = 0;
}
