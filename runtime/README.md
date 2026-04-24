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

API endpoints: `GET /api/skills`, `POST /api/plan`, `POST /api/run`.

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

17 tests cover the skill loader, planner parser, planner/LLM wiring (with a
stub), and the file-IO + shell-allowlist tool sandbox.

## Extending

- **Add a tool:** append to `builtin_tools()` in `agency/tools.py`. Each tool
  is a `Tool(name, description, input_schema, func)`.
- **Add a skill:** drop a markdown file in any category folder with the same
  YAML frontmatter as the existing personas. The loader picks it up on next
  start.
- **Swap the LLM backend:** `AnthropicLLM` is the only consumer of the SDK.
  Subclass or replace it with anything that exposes `messages_create(...)`
  returning blocks with `.type`, `.text`, `.name`, `.input`, `.id`.
