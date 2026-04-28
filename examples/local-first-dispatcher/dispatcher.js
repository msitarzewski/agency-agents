#!/usr/bin/env node
/**
 * dispatcher.js — Local-First Dispatcher for Agency Agents (Node.js reference)
 *
 * Run any agent in this repo against a LOCAL OpenAI-compatible LLM runtime
 * (Ollama, LM Studio, llama.cpp, vLLM, Apple MLX, etc.) at $0 inference cost.
 *
 * Why this exists:
 *   The agent .md files in this repo are designed to be loaded as system
 *   prompts. The conventional way is to paste them into Claude / GPT / etc.
 *   That works, but it costs API tokens per dispatch and pins your agent
 *   work to a specific cloud vendor.
 *
 *   This dispatcher reads the same agent files locally, sends them as the
 *   `system` message to a local OpenAI-compatible /v1/chat/completions
 *   endpoint, and streams back the assistant reply. Same agent definitions,
 *   $0 inference, your data never leaves the machine.
 *
 * Quick start:
 *
 *   # 1. Start any OpenAI-compatible local runtime, e.g. Ollama:
 *   ollama serve
 *   ollama pull llama3.1:8b
 *
 *   # 2. Dispatch an agent
 *   node dispatcher.js \
 *     --agent ../../engineering/backend-architect \
 *     --task "Outline a sharded Postgres schema for a multi-tenant SaaS"
 *
 *   # 3. Use a different runtime by overriding the URL + model:
 *   node dispatcher.js \
 *     --agent ../../design/whimsy-injector \
 *     --task "3 bullets on UI delight" \
 *     --base-url http://127.0.0.1:1234/v1 \
 *     --model "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF"
 *
 * Returns the assistant content on stdout. Errors and progress on stderr.
 *
 * Programmatic use:
 *
 *   import { loadAgent, dispatchAgent } from './dispatcher.js';
 *   const agent = loadAgent('../../engineering/backend-architect.md');
 *   const reply = await dispatchAgent({
 *     agent, task: 'Sketch a CDN cache invalidation strategy',
 *     baseUrl: 'http://127.0.0.1:11434/v1',
 *     model: 'llama3.1:8b',
 *   });
 *   console.log(reply.content);
 *
 * License: MIT (matches the repo).
 */

import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { join, resolve, basename } from 'node:path';
import { argv, exit, stderr, stdout } from 'node:process';

// ──────────────────────────────────────────────────────────────────────────
// Argument parsing — small, dependency-free flag parser
// ──────────────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') { out.help = true; continue; }
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next != null && !next.startsWith('--')) {
        out[key] = next; i++;
      } else {
        out[key] = true;
      }
    } else {
      out._.push(a);
    }
  }
  return out;
}

const USAGE = `dispatcher.js — Local-First Dispatcher for Agency Agents

Required:
  --agent PATH         Path to agent .md file (or directory containing one)
  --task TEXT          The task to send the agent

Optional:
  --base-url URL       OpenAI-compatible base URL (default: \$AGENCY_BASE_URL
                       or http://127.0.0.1:11434/v1 for Ollama)
  --model NAME         Model identifier (default: \$AGENCY_MODEL or "llama3.1:8b")
  --temperature FLOAT  Sampling temperature (default: 0.3 — agents tend to
                       want faithful workflow execution, not improvisation)
  --max-tokens INT     Cap on response tokens (default: 2048)
  --json               Output the full response payload as JSON instead of
                       just the assistant content
  --list DIR           List agent files under DIR (no dispatch)
  --help, -h           Show this message

Environment:
  AGENCY_BASE_URL      Default base URL
  AGENCY_MODEL         Default model
  AGENCY_API_KEY       Optional bearer (some runtimes ignore; Ollama doesn't
                       require one)

Examples:
  node dispatcher.js --list ../../engineering
  node dispatcher.js --agent ../../engineering/backend-architect \\
    --task "Sketch a sharded Postgres schema"
  node dispatcher.js --agent ../../design/whimsy-injector \\
    --task "3 bullets on UI delight" \\
    --base-url http://127.0.0.1:1234/v1 \\
    --model "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF"
`;

// ──────────────────────────────────────────────────────────────────────────
// Agent loading — parses the same frontmatter + body convention as the
// upstream agent files. Tolerant: missing or malformed frontmatter just
// means the body gets used as the system prompt verbatim.
// ──────────────────────────────────────────────────────────────────────────

/**
 * Load an agent .md file. Accepts either a direct file path or a directory
 * containing a single .md (we'll find it).
 *
 * Returns: { name, description, body, path }
 */
export function loadAgent(pathOrDir) {
  const abs = resolve(pathOrDir);
  let filePath = abs;
  if (existsSync(abs) && statSync(abs).isDirectory()) {
    const candidates = readdirSync(abs).filter(f => f.endsWith('.md'));
    if (candidates.length === 0) {
      throw new Error(`no .md files in ${abs}`);
    }
    if (candidates.length > 1) {
      throw new Error(`multiple .md files in ${abs}: ${candidates.join(', ')} — pick one`);
    }
    filePath = join(abs, candidates[0]);
  }
  if (!existsSync(filePath)) {
    // Allow `--agent foo` → `foo.md` to also work
    const withExt = filePath.endsWith('.md') ? filePath : `${filePath}.md`;
    if (existsSync(withExt)) filePath = withExt;
    else throw new Error(`agent file not found: ${filePath}`);
  }

  const raw = readFileSync(filePath, 'utf8');
  const m = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  let frontmatter = {};
  let body = raw;
  if (m) {
    body = m[2];
    for (const line of m[1].split(/\r?\n/)) {
      const kv = line.match(/^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$/);
      if (!kv) continue;
      let v = kv[2].trim();
      if ((v.startsWith('"') && v.endsWith('"')) ||
          (v.startsWith("'") && v.endsWith("'"))) {
        v = v.slice(1, -1);
      }
      frontmatter[kv[1]] = v;
    }
  }
  return {
    name: frontmatter.name || basename(filePath, '.md'),
    description: frontmatter.description || '',
    body: body.trim(),
    path: filePath,
    frontmatter,
  };
}

/**
 * List all agent files under a directory (recurses one level).
 */
export function listAgents(dir) {
  const abs = resolve(dir);
  if (!existsSync(abs) || !statSync(abs).isDirectory()) {
    throw new Error(`not a directory: ${abs}`);
  }
  const out = [];
  for (const entry of readdirSync(abs)) {
    const p = join(abs, entry);
    const st = statSync(p);
    if (st.isFile() && entry.endsWith('.md')) {
      try {
        const a = loadAgent(p);
        out.push({ name: a.name, description: a.description, path: p });
      } catch { /* skip unparseable */ }
    } else if (st.isDirectory()) {
      for (const sub of readdirSync(p)) {
        if (sub.endsWith('.md')) {
          try {
            const a = loadAgent(join(p, sub));
            out.push({ name: a.name, description: a.description, path: join(p, sub) });
          } catch {}
        }
      }
    }
  }
  return out;
}

// ──────────────────────────────────────────────────────────────────────────
// Dispatch — POST to OpenAI-compatible /v1/chat/completions
// ──────────────────────────────────────────────────────────────────────────

/**
 * Dispatch a task to an agent against a local OpenAI-compatible runtime.
 *
 * @param {object}  params
 * @param {object}  params.agent        Loaded agent (from loadAgent)
 * @param {string}  params.task         User task text
 * @param {string} [params.baseUrl]     OpenAI base URL (default Ollama :11434)
 * @param {string} [params.model]       Model id (default llama3.1:8b)
 * @param {number} [params.temperature] Default 0.3
 * @param {number} [params.maxTokens]   Default 2048
 * @param {string} [params.apiKey]      Optional bearer
 * @param {number} [params.timeoutMs]   Request timeout (default 120s)
 *
 * @returns {Promise<{ ok, content, usage?, latency_ms, model?, finish_reason? }>}
 */
export async function dispatchAgent({
  agent, task,
  baseUrl = process.env.AGENCY_BASE_URL || 'http://127.0.0.1:11434/v1',
  model = process.env.AGENCY_MODEL || 'llama3.1:8b',
  temperature = 0.3,
  maxTokens = 2048,
  apiKey = process.env.AGENCY_API_KEY,
  timeoutMs = 120_000,
}) {
  if (!agent || typeof agent !== 'object' || !agent.body) {
    return { ok: false, error: 'agent required (from loadAgent)' };
  }
  if (typeof task !== 'string' || task.trim().length === 0) {
    return { ok: false, error: 'task required (non-empty string)' };
  }

  const url = `${baseUrl.replace(/\/+$/, '')}/chat/completions`;
  const headers = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

  const body = {
    model,
    messages: [
      { role: 'system', content: agent.body },
      { role: 'user', content: task },
    ],
    temperature,
    max_tokens: maxTokens,
  };

  const t0 = Date.now();
  let resp;
  try {
    resp = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (err) {
    return {
      ok: false,
      error: 'runtime_unreachable',
      detail: err.message,
      url,
      latency_ms: Date.now() - t0,
    };
  }

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    return {
      ok: false,
      error: `runtime_http_${resp.status}`,
      detail: text.slice(0, 500),
      latency_ms: Date.now() - t0,
    };
  }

  const data = await resp.json().catch(() => null);
  if (!data) {
    return { ok: false, error: 'runtime_response_parse_failed', latency_ms: Date.now() - t0 };
  }

  return {
    ok: true,
    agent: agent.name,
    content: data.choices?.[0]?.message?.content || '',
    finish_reason: data.choices?.[0]?.finish_reason || null,
    model: data.model || model,
    usage: data.usage || null,
    latency_ms: Date.now() - t0,
  };
}

// ──────────────────────────────────────────────────────────────────────────
// CLI entrypoint
// ──────────────────────────────────────────────────────────────────────────

async function cli() {
  const args = parseArgs(argv);
  if (args.help) { stdout.write(USAGE); exit(0); }

  if (args.list) {
    const items = listAgents(args.list);
    for (const a of items) {
      stdout.write(`${a.name.padEnd(40)}  ${a.description}\n`);
    }
    exit(0);
  }

  if (!args.agent || !args.task) {
    stderr.write(USAGE);
    exit(2);
  }

  let agent;
  try { agent = loadAgent(args.agent); }
  catch (err) { stderr.write(`error: ${err.message}\n`); exit(2); }

  const result = await dispatchAgent({
    agent,
    task: args.task,
    baseUrl: args['base-url'],
    model: args.model,
    temperature: args.temperature ? parseFloat(args.temperature) : undefined,
    maxTokens: args['max-tokens'] ? parseInt(args['max-tokens'], 10) : undefined,
  });

  if (args.json) {
    stdout.write(JSON.stringify(result, null, 2) + '\n');
    exit(result.ok ? 0 : 1);
  }

  if (!result.ok) {
    stderr.write(`error: ${result.error}${result.detail ? ` — ${result.detail}` : ''}\n`);
    exit(1);
  }
  stdout.write(result.content + (result.content.endsWith('\n') ? '' : '\n'));
  stderr.write(`\n[dispatched ${agent.name} via ${result.model} in ${result.latency_ms}ms]\n`);
}

// Only run CLI if invoked directly (not when imported as a module)
if (import.meta.url === `file://${process.argv[1]}` ||
    import.meta.url.endsWith(process.argv[1])) {
  cli().catch(err => { stderr.write(`fatal: ${err.message}\n`); exit(1); });
}

export default { loadAgent, listAgents, dispatchAgent };
