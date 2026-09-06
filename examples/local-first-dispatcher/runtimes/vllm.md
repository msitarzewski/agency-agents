# vLLM setup

[vLLM](https://github.com/vllm-project/vllm) is the highest-throughput OpenAI-compatible runtime when you have a GPU. PagedAttention + continuous batching means you can dispatch many agents concurrently without per-request overhead.

Linux + NVIDIA GPU territory primarily. Also works on Mac CPU-only (slow) and AMD ROCm (with the right wheel).

## Install

```bash
# Linux + CUDA
pip install vllm                              # latest
# or pin
pip install vllm==0.6.4

# Verify
python3 -c "import vllm; print(vllm.__version__)"
```

## Start the server

```bash
# Text model
python3 -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct \
  --host 127.0.0.1 \
  --port 8000

# Quantized for tighter VRAM
python3 -m vllm.entrypoints.openai.api_server \
  --model TheBloke/Llama-3.1-8B-Instruct-AWQ \
  --quantization awq \
  --port 8000

# Big model with tensor parallelism (multi-GPU)
python3 -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3.1-70B-Instruct \
  --tensor-parallel-size 4 \
  --port 8000
```

Default endpoint: `http://127.0.0.1:8000/v1`.

## Dispatch

```bash
node dispatcher.js \
  --agent ../../engineering/backend-architect \
  --task "Sketch a sharded Postgres schema" \
  --base-url http://127.0.0.1:8000/v1 \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct
```

## Concurrency

vLLM's main win — you can dispatch dozens of agents in parallel without a serialized queue:

```js
import { loadAgent, dispatchAgent } from './dispatcher.js';

const agents = [
  loadAgent('../../engineering/backend-architect'),
  loadAgent('../../design/whimsy-injector'),
  loadAgent('../../marketing/content-creator'),
  // ... 20 more
];

const tasks = agents.map(a => dispatchAgent({
  agent: a, task: "...",
  baseUrl: 'http://127.0.0.1:8000/v1',
  model: 'meta-llama/Meta-Llama-3.1-8B-Instruct',
}));

const results = await Promise.all(tasks);   // all run concurrently
```

vLLM's continuous batching makes this almost as fast as a single sequential request, instead of N× slower.

## Notes

- For a 1× A100 80 GB: Llama-3.1-70B (4-bit) fits. 405B needs multi-GPU.
- For a 1× RTX 4090 24 GB: 8B FP16 or 32B 4-bit fits comfortably.
- If you see OOM, reduce `--max-model-len` (default 8192) or use a smaller quant.
- `--enforce-eager` disables CUDA graphs — use it on first runs to debug, then drop for prod.
