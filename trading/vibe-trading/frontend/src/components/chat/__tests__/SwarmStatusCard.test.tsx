// @vitest-environment node

import { renderToStaticMarkup } from "react-dom/server";
import { SwarmStatusCard } from "../SwarmStatusCard";
import {
  applySwarmEvent,
  buildSwarmStatusFromStarted,
  buildSwarmStatusFromToolResultPreview,
} from "@/lib/swarmStatus";
import type { SwarmRunStatus } from "@/types/agent";

function makeStatus(overrides: Partial<SwarmRunStatus> = {}): SwarmRunStatus {
  return {
    runId: "r1",
    preset: "demo_team",
    status: "running",
    currentLayer: 0,
    totalLayers: 2,
    startedAt: Date.now(),
    agents: [
      { agentId: "macro", status: "waiting", iterations: 0 },
      { agentId: "risk", status: "running", tool: "read_file", elapsed_s: 12, iterations: 2, lastText: "checking exposure" },
      { agentId: "pm", status: "done", tool: "write_file ok", elapsed_s: 30, iterations: 4, lastText: "report complete" },
      { agentId: "qa", status: "failed", error: "missing data" },
      { agentId: "ops", status: "blocked", error: "Blocked by qa" },
      { agentId: "retry_agent", status: "retry", tool: "retry 2" },
    ],
    ...overrides,
  };
}

describe("SwarmStatusCard", () => {
  it("renders agent status rows", () => {
    const html = renderToStaticMarkup(<SwarmStatusCard status={makeStatus()} />);

    expect(html).toContain("demo_team");
    expect(html).toContain("running");
    expect(html).toContain("waiting");
    expect(html).toContain("done");
    expect(html).toContain("failed");
    expect(html).toContain("blocked");
    expect(html).toContain("retry");
    expect(html).toContain("checking exposure");
    expect(html).toContain("missing data");
  });

  it("shows empty state while waiting for events", () => {
    const html = renderToStaticMarkup(<SwarmStatusCard status={makeStatus({ agents: [] })} />);

    expect(html).toContain("Waiting for agent events...");
  });

  it("builds a card model from swarm.started payload", () => {
    const status = buildSwarmStatusFromStarted({
      run_id: "r-start",
      preset: "research_team",
      status: "running",
      agents: [{ id: "analyst", role: "Analyst" }],
      tasks: [{ id: "t1", agent_id: "analyst", status: "pending" }],
    });

    expect(status?.runId).toBe("r-start");
    expect(status?.agents[0]).toMatchObject({
      agentId: "analyst",
      taskId: "t1",
      role: "Analyst",
      status: "waiting",
    });
  });

  it("updates tool and completion state from swarm events", () => {
    const initial = buildSwarmStatusFromStarted({
      run_id: "r-events",
      preset: "research_team",
      status: "running",
      agents: [{ id: "analyst", role: "Analyst" }],
      tasks: [{ id: "t1", agent_id: "analyst", status: "pending" }],
    })!;

    const started = applySwarmEvent(initial, {
      type: "task_started",
      agent_id: "analyst",
      task_id: "t1",
      data: {},
      timestamp: "2026-06-07T12:00:00Z",
    });
    const called = applySwarmEvent(started, {
      type: "tool_call",
      agent_id: "analyst",
      task_id: "t1",
      data: { tool: "read_file", iteration: 0 },
      timestamp: "2026-06-07T12:00:01Z",
    });
    const done = applySwarmEvent(called, {
      type: "task_completed",
      task_id: "t1",
      data: { iterations: 3, summary: "analysis complete" },
      timestamp: "2026-06-07T12:00:05Z",
    });

    expect(done.agents[0]).toMatchObject({
      status: "done",
      tool: "read_file",
      iterations: 3,
      lastText: "analysis complete",
    });
  });

  it("builds fallback status from run_swarm tool result preview", () => {
    const status = buildSwarmStatusFromToolResultPreview('{"status":"completed","run_id":"r-final","preset":"demo"}');

    expect(status).toMatchObject({
      runId: "r-final",
      preset: "demo",
      status: "completed",
    });
  });
});
