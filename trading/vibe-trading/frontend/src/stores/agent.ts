import { create } from "zustand";
import type { AgentMessage, SwarmRunStatus, ToolCallEntry } from "@/types/agent";

const SESSION_CACHE_MAX = 5;
const _sessionCache = new Map<string, AgentMessage[]>();

interface AgentState {
  messages: AgentMessage[];
  sessionId: string | null;
  status: "idle" | "streaming" | "error";
  streamingText: string;

  /** The session currently streaming on the backend. Survives switchSession
   *  so the sidebar spinner persists when the user navigates away. */
  streamingSessionId: string | null;

  toolCalls: ToolCallEntry[];

  sseStatus: "disconnected" | "connected" | "reconnecting";
  sseRetryAttempt: number;

  addMessage: (msg: Omit<AgentMessage, "id"> & { id?: string }) => void;
  appendDelta: (delta: string) => void;
  setStatus: (s: AgentState["status"]) => void;
  setSessionId: (id: string | null) => void;
  loadHistory: (msgs: AgentMessage[]) => void;

  addToolCall: (entry: ToolCallEntry) => void;
  updateToolCall: (id: string, update: Partial<ToolCallEntry>) => void;
  upsertSwarmStatus: (status: SwarmRunStatus) => void;
  updateSwarmStatus: (runId: string, updater: (status: SwarmRunStatus) => SwarmRunStatus) => void;

  cacheSession: (sid: string, msgs: AgentMessage[]) => void;
  getCachedSession: (sid: string) => AgentMessage[] | undefined;

  clearStreaming: () => void;

  setSseStatus: (s: AgentState["sseStatus"], retryAttempt?: number) => void;

  switchSession: (sid: string, msgs?: AgentMessage[]) => void;
  sessionLoading: boolean;
  setSessionLoading: (v: boolean) => void;

  reset: () => void;
}

let _id = 0;
const nextId = () => String(++_id);

export const useAgentStore = create<AgentState>((set) => ({
  messages: [],
  sessionId: null,
  status: "idle",
  streamingText: "",
  streamingSessionId: null,
  toolCalls: [],
  sseStatus: "disconnected",
  sseRetryAttempt: 0,
  sessionLoading: false,

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, { ...msg, id: msg.id || nextId() } as AgentMessage] })),

  appendDelta: (delta) =>
    set((s) => ({ streamingText: s.streamingText + delta })),

  setStatus: (status) =>
    set((s) => {
      const patch: Partial<AgentState> = { status };
      if (status === "streaming" && s.sessionId) {
        patch.streamingSessionId = s.sessionId;
      } else if (status !== "streaming" && s.streamingSessionId === s.sessionId) {
        patch.streamingSessionId = null;
      }
      return patch;
    }),
  setSessionId: (sessionId) => set({ sessionId }),
  loadHistory: (msgs) => set({ messages: msgs }),

  addToolCall: (entry) =>
    set((s) => ({ toolCalls: [...s.toolCalls, entry] })),
  updateToolCall: (id, update) =>
    set((s) => ({
      toolCalls: s.toolCalls.map((tc) => tc.id === id ? { ...tc, ...update } : tc),
    })),
  upsertSwarmStatus: (swarmStatus) =>
    set((s) => {
      const idx = s.messages.findIndex((m) => m.type === "swarm_status" && m.swarmRunId === swarmStatus.runId);
      if (idx >= 0) {
        const messages = [...s.messages];
        messages[idx] = { ...messages[idx], swarmStatus, timestamp: Date.now() };
        return { messages };
      }
      return {
        messages: [
          ...s.messages,
          {
            id: `swarm_${swarmStatus.runId}`,
            type: "swarm_status",
            content: "",
            swarmRunId: swarmStatus.runId,
            swarmStatus,
            timestamp: Date.now(),
          },
        ],
      };
    }),
  updateSwarmStatus: (runId, updater) =>
    set((s) => {
      const idx = s.messages.findIndex((m) => m.type === "swarm_status" && m.swarmRunId === runId && m.swarmStatus);
      if (idx < 0) return {};
      const messages = [...s.messages];
      const current = messages[idx].swarmStatus!;
      messages[idx] = { ...messages[idx], swarmStatus: updater(current), timestamp: Date.now() };
      return { messages };
    }),

  cacheSession: (sid, msgs) => {
    _sessionCache.delete(sid);
    _sessionCache.set(sid, msgs);
    if (_sessionCache.size > SESSION_CACHE_MAX) {
      const oldest = _sessionCache.keys().next().value;
      if (oldest) _sessionCache.delete(oldest);
    }
  },
  getCachedSession: (sid) => _sessionCache.get(sid),

  clearStreaming: () => set({ streamingText: "" }),

  setSseStatus: (sseStatus, retryAttempt) =>
    set({ sseStatus, sseRetryAttempt: retryAttempt ?? 0 }),

  switchSession: (sid, msgs) => {
    _id = 0;
    set((s) => ({
      sessionId: sid,
      messages: msgs || [],
      status: "idle",
      streamingText: "",
      toolCalls: [],
      sessionLoading: !msgs,
      // Preserve streamingSessionId so the sidebar spinner stays visible
      // when switching away from a running session.
      streamingSessionId: s.streamingSessionId,
    }));
  },

  setSessionLoading: (sessionLoading) => set({ sessionLoading }),

  reset: () => {
    _id = 0;
    set({
      messages: [], status: "idle", streamingText: "",
      sessionId: null, toolCalls: [], sessionLoading: false,
      streamingSessionId: null,
    });
  },
}));
