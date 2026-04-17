# Full Utilization Guide for agency-agents

This guide shows how to use **all four layers** of the repository together instead of treating it as only a prompt library.

## 1. Understand the four layers

### Agent layer — who does the work
Use the frontmatter-based agent files under directories like `engineering/`, `design/`, `marketing/`, `specialized/`, and `testing/` when you want a tool-native specialist.

### Strategy layer — how the specialists collaborate
Use `strategy/nexus-strategy.md`, `strategy/playbooks/*`, `strategy/runbooks/*`, and `strategy/coordination/*` when you want structured multi-agent execution, phase gates, handoffs, and Dev↔QA loops.

### Distribution layer — how the same roster reaches each tool
Use `scripts/convert.sh`, `scripts/install.sh`, and `integrations/README.md` to generate and install tool-specific outputs for Claude Code, Copilot, Gemini CLI, OpenCode, OpenClaw, Cursor, Aider, Windsurf, Qwen Code, and Kimi Code.

### Proof layer — what good output looks like
Use `examples/README.md` and `examples/nexus-spatial-discovery.md` as reference outputs when you want to see how parallel multi-agent work products should read.

## 2. Recommended local setup

### A. Install specialists into your primary coding tool
For Claude Code:

```bash
./scripts/install.sh --tool claude-code
```

For Cursor in a target project:

```bash
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool cursor
```

For multi-tool local usage, regenerate everything first:

```bash
./scripts/convert.sh
./scripts/install.sh
```

### B. Keep the repository itself as the strategy source of truth
Do not copy the `strategy/` documents into a tool-specific agents folder and forget them. Keep this repository available locally and reference these files directly during orchestration:

- `strategy/QUICKSTART.md`
- `strategy/nexus-strategy.md`
- `strategy/coordination/agent-activation-prompts.md`
- `strategy/coordination/handoff-templates.md`

## 3. Run a practical NEXUS-Sprint locally

### Minimal workflow
1. Read `strategy/QUICKSTART.md` and choose `NEXUS-Sprint`.
2. Use `specialized/agents-orchestrator.md` as the pipeline controller persona.
3. Copy a prompt from `strategy/coordination/agent-activation-prompts.md`.
4. Drive each implementation task through the PASS/FAIL handoff templates in `strategy/coordination/handoff-templates.md`.
5. Use `testing/testing-evidence-collector.md` and `testing/testing-reality-checker.md` to enforce evidence-based review.

### Example pattern
- **Project manager / strategist** creates the scoped backlog.
- **Frontend / backend / AI / DevOps specialists** implement one task at a time.
- **Evidence Collector** performs per-task QA.
- **Reality Checker** is the final release gate.
- **Agents Orchestrator** decides whether to advance, retry, or escalate.

## 4. Use the validation suite correctly

This repository now has three validation layers plus one combined entrypoint.

### Agent lint
Validates frontmatter-based agent assets only:

```bash
./scripts/lint-agents.sh
```

Use this after editing agent files under directories such as `engineering/`, `marketing/`, or `specialized/`.

### Strategy lint
Validates NEXUS doctrine, playbooks, runbooks, and coordination documents as documentation assets:

```bash
./scripts/lint-strategy.sh
```

Use this after editing `strategy/*`.

### Integration lint
Generates fresh temporary outputs with `convert.sh` and verifies each supported tool receives the expected artifact shape:

```bash
./scripts/lint-integrations.sh
```

Use this after editing `scripts/convert.sh`, `scripts/install.sh`, integration docs, or frontmatter structure that affects generated outputs.

### Run everything

```bash
./scripts/lint-all.sh
```

## 5. When to use each repository section

- Want a single expert persona in your editor? → use the **agent layer**.
- Want a coordinated multi-phase delivery process? → use the **strategy layer**.
- Want to install the same roster into multiple tools? → use the **distribution layer**.
- Want examples of high-quality multi-agent output? → use the **proof layer**.

Treating only one layer as “the project” leaves a lot of value unused. The strongest usage pattern is to install the specialists into your tool **and** keep the NEXUS strategy documents nearby as the operating manual.
