# Ollama setup

[Ollama](https://ollama.com) is the easiest way to run an OpenAI-compatible LLM runtime locally. Single binary, simple model pulls, works on macOS / Linux / Windows.

## Install

```bash
# macOS — homebrew
brew install ollama

# macOS / Linux — script
curl -fsSL https://ollama.com/install.sh | sh
```

## Start the server

```bash
ollama serve   # foreground; or run as a background service
```

By default Ollama listens on `127.0.0.1:11434`. Its OpenAI-compatible endpoint is at `http://127.0.0.1:11434/v1`.

## Pull a model

Pick whatever fits your RAM. Rough rule for 4-bit-quantized models: ~`size_in_billions × 0.6` GB.

| Hardware | Recommended | Pull command |
| --- | --- | --- |
| 8 GB RAM | llama3.2:3b | `ollama pull llama3.2:3b` |
| 16 GB RAM | llama3.1:8b | `ollama pull llama3.1:8b` |
| 32 GB RAM | qwen2.5:14b | `ollama pull qwen2.5:14b` |
| 64 GB+ RAM | llama3.3:70b | `ollama pull llama3.3:70b` |
| Coding focus | qwen2.5-coder:7b or 32b | `ollama pull qwen2.5-coder:32b` |

## Dispatch

```bash
node dispatcher.js \
  --agent ../../engineering/backend-architect \
  --task "Sketch a sharded Postgres schema" \
  --base-url http://127.0.0.1:11434/v1 \
  --model llama3.1:8b
```

Or set the env once:

```bash
export AGENCY_BASE_URL=http://127.0.0.1:11434/v1
export AGENCY_MODEL=llama3.1:8b
node dispatcher.js --agent ../../engineering/backend-architect --task "..."
```

## Concurrency

By default Ollama serializes requests. To allow parallel dispatch:

```bash
OLLAMA_NUM_PARALLEL=4 ollama serve
```

Watch RAM — each parallel slot keeps its own KV cache. Halve the parallel count if you see swap thrash.

## Keepalive

Ollama unloads models from VRAM after 5 minutes idle. To keep a model warm:

```bash
OLLAMA_KEEP_ALIVE=24h ollama serve
```

Or pass `keep_alive` in each request body if your wrapper exposes it.

## Notes

- The dispatcher uses the OpenAI-compatible `/v1/chat/completions` endpoint, not Ollama's native `/api/chat`. Both work; OpenAI-compat lets you swap runtimes without touching dispatcher code.
- `temperature` and `max_tokens` flow through unchanged.
- `usage.total_tokens` is reported reliably as of Ollama 0.3.0+.
