# Apple MLX setup

[MLX](https://github.com/ml-explore/mlx) is Apple's array framework optimized for Apple Silicon. The `mlx-lm` package ships an OpenAI-compatible server that runs faster than llama.cpp on M-series chips because it talks directly to Metal.

This is the runtime that powers the production deployment behind this dispatcher (EDHAT Studios, ~250 agents/day, $0).

## Install

```bash
# In a venv (recommended)
python3 -m venv ~/venvs/mlx
source ~/venvs/mlx/bin/activate
pip install mlx-lm           # text models only
pip install mlx-vlm          # text + vision models (Gemma 3, Qwen3-VL, etc.)
```

## Pull a model

MLX uses HuggingFace under the hood. Browse [`mlx-community`](https://huggingface.co/mlx-community) for ready-converted models. Examples:

```bash
# Text-only — small, fast
huggingface-cli download mlx-community/Llama-3.1-8B-Instruct-4bit

# Larger reasoning model
huggingface-cli download mlx-community/Qwen2.5-32B-Instruct-4bit

# Vision-capable (use mlx-vlm)
huggingface-cli download mlx-community/gemma-3-27b-it-4bit
```

Files land under `~/.cache/huggingface/hub/`.

## Start the server

```bash
# Text-only models
mlx_lm.server \
  --model mlx-community/Llama-3.1-8B-Instruct-4bit \
  --host 127.0.0.1 \
  --port 8080

# Vision-capable models (also handles text)
python3 -m mlx_vlm.server \
  --model mlx-community/gemma-3-27b-it-4bit \
  --host 127.0.0.1 \
  --port 8080 \
  --trust-remote-code
```

Default endpoint: `http://127.0.0.1:8080/v1`.

## Dispatch

```bash
node dispatcher.js \
  --agent ../../engineering/backend-architect \
  --task "Sketch a sharded Postgres schema" \
  --base-url http://127.0.0.1:8080/v1 \
  --model mlx-community/Llama-3.1-8B-Instruct-4bit
```

## Performance reference (Apple M2 Ultra, 128 GB)

| Model | RAM | Tokens/sec | Notes |
| --- | --- | --- | --- |
| Llama-3.1-8B-Instruct-4bit | 5 GB | 75-90 | Fast default |
| Qwen2.5-32B-Instruct-4bit | 19 GB | 35-45 | Stronger reasoning |
| gemma-3-27b-it-4bit | 16 GB | 60-70 | Best vision/text combo |
| Llama-3.3-70B-Instruct-4bit | 40 GB | 18-25 | Frontier-adjacent quality |

## Notes

- MLX uses Apple's unified memory — RAM == VRAM. You can run a 70B model on a 64 GB Mac, but expect swap pressure.
- mlx_lm.server **doesn't have an idle-timeout flag** — model stays in RAM until the process dies. To free RAM, kill and respawn.
- Cold start (first request after server boot): 5-15 seconds for an 8B model, 25-45s for a 70B.
- Vision: `mlx_vlm.server` accepts OpenAI-style `image_url` content blocks.
- Adapter loading: pass `--adapter-path /path/to/lora-adapter` to mount a LoRA.
