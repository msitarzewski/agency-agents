import type {
  SwarmAgentDisplayStatus,
  SwarmAgentStatus,
  SwarmRunStatus,
} from "@/types/agent";

type AnyRecord = Record<string, unknown>;

function asRecord(value: unknown): AnyRecord {
  return value && typeof value === "object" ? value as AnyRecord : {};
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function timestampMs(value: unknown, fallback = Date.now()): number {
  if (typeof value !== "string") return fallback;
  const parsed = new Date(value).getTime();
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeRunStatus(value: unknown): SwarmRunStatus["status"] {
  const status = asString(value, "unknown");
  if (["pending", "running", "completed", "failed", "cancelled"].includes(status)) {
    return status as SwarmRunStatus["status"];
  }
  return "unknown";
}

function mapTaskStatus(value: unknown): SwarmAgentDisplayStatus {
  switch (asString(value)) {
    case "in_progress":
      return "running";
    case "completed":
      return "done";
    case "failed":
      return "failed";
    case "blocked":
      return "blocked";
    case "cancelled":
      return "cancelled";
    case "pending":
    default:
      return "waiting";
  }
}

function eventAgentKey(event: AnyRecord): { agentId: string; taskId?: string } {
  const data = asRecord(event.data);
  return {
    agentId: asString(event.agent_id) || asString(data.agent_id),
    taskId: asString(event.task_id) || asString(data.task_id) || undefined,
  };
}

function updateAgent(
  status: SwarmRunStatus,
  selector: { agentId?: string; taskId?: string },
  update: (agent: SwarmAgentStatus) => SwarmAgentStatus,
): SwarmRunStatus {
  const idx = status.agents.findIndex((agent) => (
    (selector.taskId && agent.taskId === selector.taskId) ||
    (selector.agentId && agent.agentId === selector.agentId)
  ));
  if (idx < 0) {
    if (!selector.agentId) return status;
    return {
      ...status,
      agents: [
        ...status.agents,
        update({ agentId: selector.agentId, taskId: selector.taskId, status: "waiting" }),
      ],
    };
  }

  const agents = [...status.agents];
  agents[idx] = update(agents[idx]);
  return { ...status, agents };
}

export function buildSwarmStatusFromStarted(data: AnyRecord, now = Date.now()): SwarmRunStatus | null {
  const runId = asString(data.run_id);
  if (!runId) return null;

  const agentMeta = new Map<string, { role?: string }>();
  const agentsRaw = Array.isArray(data.agents) ? data.agents : [];
  for (const item of agentsRaw) {
    const agent = asRecord(item);
    const id = asString(agent.id);
    if (id) agentMeta.set(id, { role: asString(agent.role) || undefined });
  }

  const tasksRaw = Array.isArray(data.tasks) ? data.tasks : [];
  const agents: SwarmAgentStatus[] = tasksRaw.map((item) => {
    const task = asRecord(item);
    const agentId = asString(task.agent_id);
    const meta = agentMeta.get(agentId);
    return {
      agentId,
      taskId: asString(task.id) || undefined,
      role: meta?.role,
      status: mapTaskStatus(task.status),
      iterations: asNumber(task.worker_iterations) ?? 0,
      lastText: asString(task.summary) || undefined,
      error: asString(task.error) || undefined,
    };
  }).filter((agent) => agent.agentId);

  for (const [agentId, meta] of agentMeta) {
    if (!agents.some((agent) => agent.agentId === agentId)) {
      agents.push({ agentId, role: meta.role, status: "waiting", iterations: 0 });
    }
  }

  return {
    runId,
    preset: asString(data.preset) || asString(data.preset_name) || "swarm",
    status: normalizeRunStatus(data.status),
    currentLayer: 0,
    totalLayers: 0,
    startedAt: now,
    agents,
  };
}

export function applySwarmEvent(current: SwarmRunStatus, rawEvent: unknown, now = Date.now()): SwarmRunStatus {
  const event = asRecord(rawEvent);
  const data = asRecord(event.data);
  const type = asString(event.type);
  const eventTime = timestampMs(event.timestamp, now);
  const { agentId, taskId } = eventAgentKey(event);

  if (type === "layer_started") {
    const layer = asNumber(data.layer) ?? current.currentLayer;
    return {
      ...current,
      status: "running",
      currentLayer: layer,
      totalLayers: Math.max(current.totalLayers, layer + 1),
    };
  }

  if (type === "run_started") {
    return { ...current, status: "running", startedAt: current.startedAt || eventTime };
  }

  if (type === "run_completed") {
    return {
      ...current,
      status: normalizeRunStatus(data.status),
      completedAt: eventTime,
    };
  }

  if (type === "run_error") {
    return { ...current, status: "failed", completedAt: eventTime };
  }

  if (type === "task_started" || type === "worker_started") {
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      agentId: agent.agentId || agentId,
      taskId: agent.taskId || taskId,
      status: "running",
      startedAt: eventTime,
    }));
  }

  if (type === "tool_call") {
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      status: "running",
      tool: asString(data.tool, agent.tool || "?"),
      iterations: Math.max(agent.iterations ?? 0, (asNumber(data.iteration) ?? (agent.iterations ?? 0)) + 1),
    }));
  }

  if (type === "tool_result") {
    return updateAgent(current, { agentId, taskId }, (agent) => {
      const tool = asString(data.tool, agent.tool || "?");
      const ok = asString(data.status, "ok") === "ok";
      return {
        ...agent,
        tool: `${tool} ${ok ? "ok" : "error"}`,
        elapsed_s: (asNumber(data.elapsed_ms) ?? 0) / 1000 || agent.elapsed_s,
      };
    });
  }

  if (type === "task_heartbeat") {
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      status: agent.status === "waiting" ? "running" : agent.status,
      tool: asString(data.tool, agent.tool || ""),
      elapsed_s: asNumber(data.elapsed_s) ?? agent.elapsed_s,
    }));
  }

  if (type === "worker_text") {
    const content = asString(data.content).trim();
    const lastLine = content.split("\n").map((line) => line.trim()).filter(Boolean).pop();
    if (!lastLine) return current;
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      lastText: lastLine.slice(0, 160),
    }));
  }

  if (type === "task_completed" || type === "worker_completed") {
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      status: "done",
      elapsed_s: agent.startedAt ? Math.max(0, (eventTime - agent.startedAt) / 1000) : agent.elapsed_s,
      iterations: asNumber(data.iterations) ?? agent.iterations,
      lastText: asString(data.summary) || agent.lastText,
    }));
  }

  if (["task_failed", "worker_failed", "worker_timeout", "worker_incomplete"].includes(type)) {
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      status: "failed",
      elapsed_s: agent.startedAt ? Math.max(0, (eventTime - agent.startedAt) / 1000) : agent.elapsed_s,
      error: asString(data.error) || asString(data.reason) || agent.error,
    }));
  }

  if (type === "task_blocked") {
    const blockedBy = Array.isArray(data.blocked_by) ? data.blocked_by.join(", ") : asString(data.reason);
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      status: "blocked",
      error: blockedBy ? `Blocked by ${blockedBy}` : agent.error,
    }));
  }

  if (type === "task_retry") {
    const attempt = asNumber(data.attempt);
    return updateAgent(current, { agentId, taskId }, (agent) => ({
      ...agent,
      status: "retry",
      tool: attempt ? `retry ${attempt}` : "retry",
    }));
  }

  return current;
}

export function buildSwarmStatusFromToolResultPreview(preview: string, now = Date.now()): SwarmRunStatus | null {
  if (!preview.includes("run_id") && !preview.includes("preset")) return null;

  try {
    const parsed = JSON.parse(preview) as AnyRecord;
    const runId = asString(parsed.run_id);
    if (!runId) return null;
    return {
      runId,
      preset: asString(parsed.preset) || "swarm",
      status: normalizeRunStatus(parsed.status),
      currentLayer: 0,
      totalLayers: 0,
      startedAt: now,
      completedAt: ["completed", "failed", "cancelled"].includes(asString(parsed.status)) ? now : undefined,
      agents: [],
    };
  } catch {
    const runId = preview.match(/"run_id"\s*:\s*"([^"]+)"/)?.[1];
    if (!runId) return null;
    const preset = preview.match(/"preset"\s*:\s*"([^"]+)"/)?.[1] || "swarm";
    const rawStatus = preview.match(/"status"\s*:\s*"([^"]+)"/)?.[1] || "unknown";
    const status = normalizeRunStatus(rawStatus);
    return {
      runId,
      preset,
      status,
      currentLayer: 0,
      totalLayers: 0,
      startedAt: now,
      completedAt: ["completed", "failed", "cancelled"].includes(status) ? now : undefined,
      agents: [],
    };
  }
}
