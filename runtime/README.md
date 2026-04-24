# Agency Runtime

A Python orchestration runtime that turns the persona markdown files in this
repo into runnable skills. Pick (or auto-route to) any of the 180+ agents,
hand it a request, and the runtime drives a Claude tool-use loop with file IO,
sandboxed shell, and web fetch.

## What this is — and isn't

- **Is:** a thin runtime that *uses* the existing `*.md` persona library as
  system prompts, plus a planner, executor, CLI, and web UI.
- **Isn't:** a replacement for the existing installer scripts. They still copy
  agent files into Claude Code, Cursor, etc. This adds a runtime so you can run
  the agents directly from this repo.

## Install

```bash
pip install -e runtime            # base runtime
pip install -e 'runtime[docs]'    # add PDF / DOCX / XLSX extraction
pip install -e 'runtime[dev]'     # add pytest
export ANTHROPIC_API_KEY=sk-ant-...
```

### Config via env

| Variable | Effect |
|---|---|
| `AGENCY_MODEL` | Override execution model (default `claude-opus-4-7`). |
| `AGENCY_PLANNER_MODEL` | Override planner model (default `claude-haiku-4-5`). |
| `AGENCY_MAX_TOKENS` | Per-request `max_tokens` (default 16000). |
| `AGENCY_TASK_BUDGET` | If ≥ 20000, pass `output_config.task_budget` (Opus 4.7 beta). Agent self-moderates within this token budget across a loop. |
| `AGENCY_MCP_SERVERS` | JSON list of MCP server configs. When set, the runtime switches to `client.beta.messages` with the `mcp-client-2025-11-20` beta header. |
| `AGENCY_ENABLE_WEB_SEARCH=1` | Register Anthropic's hosted `web_search_20260209` tool. |
| `AGENCY_ENABLE_CODE_EXECUTION=1` | Register the hosted Python sandbox `code_execution_20260120`. |
| `AGENCY_ENABLE_COMPUTER_USE=1` | Enable mouse/keyboard/screenshot via `pip install -e 'runtime[computer]'`. Requires a display. |
| `AGENCY_ALLOW_SHELL=1` | Opt into the allowlisted shell tool. |
| `AGENCY_NO_NETWORK=1` | Disable `web_fetch`. |
| `AGENCY_TOOL_TIMEOUT` | Per-tool wall-clock seconds (default 30). |

Example MCP config:

```bash
export AGENCY_MCP_SERVERS='[
  {"type": "url", "name": "github", "url": "https://api.githubcopilot.com/mcp/"}
]'
```

## Use

### Browse skills

```bash
agency list
agency list --category engineering
agency list --search "frontend"
```

### See who would handle a request

```bash
agency plan "design a brand identity for a B2B SaaS startup"
```

### Run a request end to end

```bash
agency run "review the security of this code base"
agency run "..." --skill engineering-frontend-developer   # force a skill
agency run "..." --session my-project                    # remember context
agency run "..." --show-usage                            # print token totals
```

### Scaffold a new persona

```bash
agency init my-slug --name "My Agent" --category specialized --emoji 🎯
```

### Diagnose the environment

```bash
agency doctor
```

Shows loaded skills per category, which env flags are set, which optional
deps (`[docs]`, `[computer]`) are installed, and the tool context defaults.
Run it first if something isn't working.

### Debug the tool-use loop

```bash
agency debug "list the files in this repo"
```

### Web UI

```bash
agency serve --port 8765
# open http://127.0.0.1:8765
```

API endpoints:
- `GET /api/skills` — list loaded skills
- `POST /api/plan` — `{"message": "..."}` → which skill the planner picks
- `POST /api/run` — `{"message": "...", "skill"?: "...", "session_id"?: "..."}` → final text
- `POST /api/run/stream` — same body, streamed as Server-Sent Events
  (`plan`, `text_delta`, `tool_use`, `tool_result`, `stop`, `done`, `error`)

## Architecture

```
runtime/agency/
  skills.py     — discover *.md persona files, parse frontmatter
  llm.py        — Anthropic SDK wrapper (caches the persona system prompt,
                  task-budget + MCP passthrough, config from env)
  tools.py      — read_file, write_file, edit_file, list_dir, extract_doc,
                  run_shell, web_fetch, list_skills, plan, delegate_to_skill
  planner.py    — keyword shortlist → Haiku picks the best skill
  executor.py   — tool-use loop (streaming + non-streaming), parallel-safe
                  tool fan-out, usage tracking, plan binding, memory
  memory.py     — JSONL session store under ~/.agency/sessions/
  cli.py        — Click CLI: list, plan, run, debug, serve, init
  server.py     — FastAPI + streaming chat UI
```

### Defaults

- **Models:** `claude-opus-4-7` for execution, `claude-haiku-4-5` for planning.
- **Prompt caching:** the persona body is sent as a cached system prompt, so
  subsequent turns of a session are billed at the cache-read rate.
- **Tool sandbox:** all file paths are resolved against the workdir and
  rejected if they escape it. Shell is off by default; when enabled, only
  commands whose head is in the allowlist (`ls`, `cat`, `git`, `grep`,
  `python3`, etc.) run.

## Tests

```bash
cd runtime && python3 -m pytest
```

The test suite covers the skill loader, planner (parser + LLM wiring with a
stub), the file-IO + shell-allowlist tool sandbox, edit_file, extract_doc,
the plan tool, the executor's non-streaming and streaming tool-use loops,
token-usage accumulation, parallel-safe tool fan-out, session-memory
round-trips, delegation between skills, LLM config + task-budget + MCP
routing, the CLI (Click `CliRunner`), and the server endpoints (FastAPI
`TestClient`).

## Delegation

Agents can hand off to each other via the `delegate_to_skill` tool. The
executor exposes it by default. Delegation is capped at depth 2 so a chain
like *strategy → engineering → writing* is allowed but can't recurse
indefinitely.

## Persistent plan (per-session scratchpad)

When a session id is set, agents get a `plan` tool that reads/writes a
markdown file under `~/.agency/plans/<session_id>.md`. Use it for long
tasks: the agent decomposes the work up front, checks items off as it
goes, and re-reads the plan between turns so it stays on track.

Actions: `view`, `write`, `append`, `clear`.
Inspired by the Manus-style planning pattern.

## Docker

```bash
docker build -f runtime/Dockerfile -t agency-runtime .
docker run --rm -p 8765:8765 -e ANTHROPIC_API_KEY=... agency-runtime
# CLI usage:
docker run --rm -e ANTHROPIC_API_KEY=... agency-runtime agency list
```

## Extending

- **Add a tool:** append to `builtin_tools()` in `agency/tools.py`. Each tool
  is a `Tool(name, description, input_schema, func)`.
- **Add a skill:** drop a markdown file in any category folder with the same
  YAML frontmatter as the existing personas. The loader picks it up on next
  start.
- **Swap the LLM backend:** `AnthropicLLM` is the only consumer of the SDK.
  Subclass or replace it with anything that exposes `messages_create(...)`
  returning blocks with `.type`, `.text`, `.name`, `.input`, `.id`.
