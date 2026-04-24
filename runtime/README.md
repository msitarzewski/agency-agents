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
pip install -e runtime
export ANTHROPIC_API_KEY=sk-ant-...
```

Optional:

```bash
export AGENCY_ALLOW_SHELL=1   # opt in to allowlisted shell tool
export AGENCY_NO_NETWORK=1    # disable the web_fetch tool
export AGENCY_TOOL_TIMEOUT=30 # per-tool wall clock
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
```

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
  llm.py        — Anthropic SDK wrapper (caches the persona system prompt)
  tools.py      — read_file, write_file, list_dir, run_shell, web_fetch, list_skills
  planner.py    — keyword shortlist → Haiku picks the best skill
  executor.py   — tool-use loop with optional on-disk session memory
  memory.py     — JSONL session store under ~/.agency/sessions/
  cli.py        — Click CLI: list, plan, run, debug, serve
  server.py     — FastAPI + minimal HTML chat UI
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

39 tests cover the skill loader, planner (parser + LLM wiring with a stub),
the file-IO + shell-allowlist tool sandbox, the plan tool, the executor's
non-streaming and streaming tool-use loops, session-memory round-trips,
delegation between skills, the CLI (Click `CliRunner`), and the server
endpoints (FastAPI `TestClient`).

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
