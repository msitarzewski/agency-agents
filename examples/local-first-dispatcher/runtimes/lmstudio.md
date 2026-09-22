# LM Studio setup

[LM Studio](https://lmstudio.ai) is a desktop app for running local LLMs with a Chat UI and an OpenAI-compatible server mode. Good fit if you want a GUI for browsing/loading models alongside CLI dispatch.

## Install

Download the macOS / Windows / Linux installer from <https://lmstudio.ai>. Run it.

## Load a model

1. Open the **Discover** tab in the app.
2. Search for a model (e.g. `meta-llama/Meta-Llama-3.1-8B-Instruct-GGUF`, `lmstudio-community/Qwen2.5-Coder-32B-Instruct-GGUF`).
3. Click **Download**, pick a quantization (Q4_K_M is a good default), wait.
4. Switch to the **Chat** tab, click the model picker at top, select your model.

## Start the server

In the app:

1. Click the **Developer** tab (icon: `< >`).
2. Click **Start Server**.

Default endpoint: `http://127.0.0.1:1234/v1`. The model identifier shows in the top bar — use that exact string in your dispatcher call.

## Dispatch

```bash
node dispatcher.js \
  --agent ../../design/whimsy-injector \
  --task "3 bullets on UI delight" \
  --base-url http://127.0.0.1:1234/v1 \
  --model "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF"
```

Note: LM Studio is finicky about the model id. Copy/paste from the app's chat UI top bar — case-sensitive, slashes included.

## Headless mode (no GUI)

LM Studio ships a CLI:

```bash
# Start headless server with a specific model
lms server start
lms load <model-name>
```

Reference: <https://lmstudio.ai/docs/cli>.

## Notes

- LM Studio's server is fast (~50-150 tok/s on Apple Silicon for an 8B 4-bit model).
- Concurrency: single-stream by default. Larger machines can run multiple LM Studio instances on different ports.
- Cold start: ~3-5 seconds per model (depends on quantization + hardware).
