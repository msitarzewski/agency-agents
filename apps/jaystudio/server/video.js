// Video studio: brief -> spec (LLM) -> estimate -> submit -> poll -> result, via the video-toolkit MCP server.
import * as hub from "./mcp-hub.js";
import { assertBudget, record } from "./costs.js";
import { insert, readCollection, update, findById } from "./store.js";
import { emit } from "./events.js";

const SERVER = "video-toolkit";

async function call(tool, args) {
  const res = await hub.callTool(SERVER, tool, args, 120_000);
  const data = hub.resultJson(res);
  if (res.isError) throw new Error(data?.error || data?.text || `${tool} thất bại`);
  return data;
}

export const presets = () => call("video_list_presets", {});

export async function estimate(spec) {
  return call("video_estimate", { spec });
}

function estimateUsd(e) {
  return Number(e?.total_usd ?? e?.estimate?.total_usd ?? e?.usd ?? 0) || 0;
}

export async function submit({ spec, maxUsd = 2, brandId }) {
  const est = await estimate(spec);
  assertBudget(estimateUsd(est));
  const job = await call("video_submit", { spec, max_usd: maxUsd });
  const jobId = job?.job_id || job?.id;
  record({ task: "video", tier: "video-toolkit", model: "video-toolkit", costUsd: estimateUsd(job?.estimate || est), note: `job ${jobId} (ước tính)` });
  insert("videos", { id: jobId, brandId: brandId || null, title: spec?.title || "Video", spec, estimate: est, status: "queued", createdAt: new Date().toISOString() });
  emit("video.job.submitted", { jobId, brandId: brandId || null, title: spec?.title || "Video", estimateUsd: estimateUsd(est) });
  return { jobId, job, estimate: est };
}

export async function status(jobId) {
  const s = await call("video_status", { job_id: jobId });
  const phase = s?.phase || s?.status || "unknown";
  const prev = findById("videos", jobId)?.status;
  update("videos", jobId, { status: phase });
  if (phase === "failed" && prev !== "failed") emit("video.job.failed", { jobId, resumable: Boolean(s?.resumable), warnings: s?.warnings || [] });
  return s;
}

export async function result(jobId) {
  const r = await call("video_result", { job_id: jobId });
  const prev = findById("videos", jobId);
  update("videos", jobId, { status: "done", result: r });
  if (!prev?.result) emit("video.job.completed", { jobId, brandId: prev?.brandId || null, title: prev?.title, result: r });
  return r;
}

export const cancel = (jobId) => call("video_cancel", { job_id: jobId });
export const resume = (jobId, maxUsd) => call("video_resume", { job_id: jobId, max_usd: maxUsd ?? null });
export const list = () => readCollection("videos").slice().reverse();
