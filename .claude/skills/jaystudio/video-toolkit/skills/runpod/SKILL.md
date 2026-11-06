---
name: runpod
description: Cloud GPU processing via RunPod serverless. Use when setting up RunPod endpoints, deploying Docker images, managing GPU resources, troubleshooting endpoint issues, or understanding costs. Covers all 5 toolkit images (qwen-edit, realesrgan, propainter, sadtalker, qwen3-tts).
---

# RunPod Cloud GPU

Run open-source AI models on cloud GPUs via RunPod serverless. Pay-per-second, no minimums.

## Setup

```bash
# 1. Create account at https://runpod.io
# 2. Add API key to .env
echo "RUNPOD_API_KEY=your_key_here" >> .env

# 3. Deploy any tool with --setup
uv run tools/image_edit.py --setup
uv run tools/upscale.py --setup
uv run tools/dewatermark.py --setup
uv run tools/sadtalker.py --setup
uv run tools/qwen3_tts.py --setup
```

Each `--setup` command:
1. Creates a RunPod **template** from the Docker image
2. Creates a serverless **endpoint** with appropriate GPU
3. Saves the endpoint ID to `.env` (e.g. `RUNPOD_QWEN_EDIT_ENDPOINT_ID`)

## Available Images

All images are public on GHCR — no authentication needed.

| Tool | Docker Image | GPU | VRAM | Typical Cost |
|------|-------------|-----|------|-------------|
| image_edit | `ghcr.io/conalmullan/video-toolkit-qwen-edit:latest` | A6000/L40S | 48GB+ | ~$0.05-0.15/job |
| upscale | `ghcr.io/conalmullan/video-toolkit-realesrgan:latest` | RTX 3090/4090 | 24GB | ~$0.01-0.05/job |
| dewatermark | `ghcr.io/conalmullan/video-toolkit-propainter:latest` | RTX 3090/4090 | 24GB | ~$0.05-0.30/job |
| sadtalker | `ghcr.io/conalmullan/video-toolkit-sadtalker:latest` | RTX 4090 | 24GB | ~$0.05-0.15/job |
| qwen3_tts | `ghcr.io/conalmullan/video-toolkit-qwen3-tts:latest` | ADA 24GB | 24GB | ~$0.01-0.05/job |

**Total monthly cost:** Rarely exceeds $10 even with heavy use.

## How It Works

All tools follow the same pattern:

```
Local CLI → Upload input to cloud storage → RunPod API → Poll for result → Download output
```

1. **File transfer:** Tools use Cloudflare R2 when configured (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`), falling back to free upload services
2. **RunPod API:** Tools call the `/run` endpoint, then poll `/status/{job_id}` until complete
3. **Cold vs warm start:** First request after idle spins up a worker (~30-90s). Subsequent requests are fast (~5-15s)

## Endpoint Management

### Workers

```
workersMin: 0    — Scale to zero when idle (no cost)
workersMax: 1    — Max concurrent jobs (increase for throughput)
idleTimeout: 5   — Seconds before worker scales down
```

Across all endpoints, you share a total worker pool based on your RunPod plan. If you hit limits, reduce `workersMax` on endpoints you're not actively using.

### Checking Endpoint Status

Each tool stores its endpoint ID in `.env`:

| Tool | Env Var |
|------|---------|
| image_edit | `RUNPOD_QWEN_EDIT_ENDPOINT_ID` |
| upscale | `RUNPOD_UPSCALE_ENDPOINT_ID` |
| dewatermark | `RUNPOD_DEWATERMARK_ENDPOINT_ID` |
| sadtalker | `RUNPOD_SADTALKER_ENDPOINT_ID` |
| qwen3_tts | `RUNPOD_QWEN3_TTS_ENDPOINT_ID` |

### Disabling an Endpoint

To free worker slots without deleting the endpoint, set `workersMax=0` via the RunPod dashboard or GraphQL API.

## RunPod API Reference

Use these to query and manage endpoints programmatically. RunPod disables GraphQL introspection, so these field names are verified and must be exact.

### Authentication

All API calls require `Authorization: Bearer $RUNPOD_API_KEY`.

- **GraphQL:** `POST https://api.runpod.io/graphql`
- **REST (Serverless):** `https://api.runpod.ai/v2/{endpoint_id}/...`

### GraphQL Queries

**List all endpoints:**
```graphql
query { myself { endpoints { id name gpuIds templateId workersMax workersMin } } }
```

**Current spend rate:**
```graphql
query { myself { currentSpendPerHr spendDetails { localStoragePerHour networkStoragePerHour gpuComputePerHour } } }
```

**List pods:**
```graphql
query { myself { pods { id name runtime { uptimeInSeconds } machine { gpuDisplayName } desiredStatus } } }
```

> **Common mistakes:** Field names are camelCase with full words — `localStoragePerHour` not `localStoragePerHr`. Endpoints are `endpoints` not `serverlessWorkers`. `spending` is not a field — use `currentSpendPerHr` and `spendDetails`.

### GraphQL Mutations

**Update endpoint GPU or config:**
```graphql
mutation { saveEndpoint(input: {
  id: "endpoint_id",
  name: "endpoint-name",
  templateId: "template_id",
  gpuIds: "AMPERE_24",
  workersMin: 0,
  workersMax: 1
}) { id gpuIds } }
```

`saveEndpoint` requires `name` and `templateId` even for updates — query first to get current values.

### REST API (Serverless)

| Action | Method | URL |
|--------|--------|-----|
| Submit job | POST | `/v2/{id}/run` |
| Check status | GET | `/v2/{id}/status/{job_id}` |
| Cancel job | POST | `/v2/{id}/cancel/{job_id}` |
| List pending | GET | `/v2/{id}/requests` |
| Health/stats | GET | `/v2/{id}/health` |

**Health response** includes job counts and worker state:
```json
{
  "jobs": { "completed": 16, "failed": 1, "inProgress": 0, "inQueue": 2, "retried": 0 },
  "workers": { "idle": 0, "initializing": 1, "ready": 0, "running": 0, "throttled": 0 }
}
```

> **Note:** `/requests` only returns pending/queued jobs. Completed job history is not available via the API — check the RunPod web console for logs.

### GPU Type IDs

| ID | GPU | VRAM | Typical Cost |
|----|-----|------|-------------|
| `AMPERE_24` | RTX 3090 | 24GB | ~$0.34/hr |
| `ADA_24` | RTX 4090 | 24GB | ~$0.69/hr |
| `AMPERE_48` | A6000 | 48GB | ~$0.76/hr |
| `AMPERE_80` | A100 | 80GB | ~$1.99/hr |

**Availability note:** `ADA_24` (4090) is frequently throttled/unavailable on RunPod. Always configure endpoints with **multiple fallback GPU types** (comma-separated) to avoid jobs getting stuck in queue indefinitely:

```graphql
gpuIds: "AMPERE_24,ADA_24"   # Try 3090 first, fall back to 4090
```

All toolkit tools also enforce a 5-minute queue timeout — if no GPU is available within 300 seconds, the job is automatically cancelled to prevent runaway billing from failed initialization cycles.

### Cloudflare R2 via AWS CLI

R2 uses the S3-compatible API but requires `--region auto`:

```bash
AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
aws s3api list-objects-v2 \
  --bucket "$R2_BUCKET_NAME" \
  --endpoint-url "https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com" \
  --region auto
```

> **Common mistake:** Omitting `--region auto` causes `InvalidRegionName` error. R2 valid regions: `wnam`, `enam`, `weur`, `eeur`, `apac`, `oc`, `auto`.

## Troubleshooting

### Force Image Pull

When you push a new Docker image version, RunPod may still use the cached old one. To force a pull:

1. Update the template's `imageName` to use `@sha256:DIGEST` notation
2. Wait for the worker to restart
3. Revert to `:latest` tag after confirming

### Cold Start Too Slow

- **qwen3-tts:** ~70s cold start, ~7s warm
- **sadtalker:** ~60s cold start, ~10s warm
- **image_edit:** ~90s cold start, ~15s warm

If cold starts are a problem, set `workersMin: 1` (costs money when idle).

### Job Fails with OOM

The model needs more VRAM than the GPU provides. Options:
- Use a larger GPU tier
- For dewatermark: reduce `--resize-ratio` (default 0.5 for safety)
- For image_edit: reduce `--steps`

### "No workers available"

You've hit your plan's concurrent worker limit. Either:
- Wait for a running job to finish
- Set `workersMax=0` on endpoints you're not using
- Upgrade your RunPod plan

## Docker Images

All Dockerfiles live in `docker/runpod-*/`. Images use `runpod/pytorch` as the base to share layers across tools.

Building for RunPod (from Apple Silicon Mac):
```bash
docker buildx build --platform linux/amd64 -t ghcr.io/conalmullan/video-toolkit-<name>:latest docker/runpod-<name>/
docker push ghcr.io/conalmullan/video-toolkit-<name>:latest
```

GHCR packages default to **private** — you must manually make them public for RunPod to pull them. Go to GitHub > Packages > Package Settings > Change Visibility.

## Cost Optimization

- Keep `workersMin: 0` on all endpoints (scale to zero)
- Only deploy endpoints you actively need
- Use `workersMax=0` to disable idle endpoints without deleting them
- Qwen3-TTS is significantly cheaper than ElevenLabs for voiceovers
- Check the RunPod dashboard for usage and billing
