/// <reference types="vitest" />
import { describe, it, expect } from 'vitest';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildSwarm } from '../src/swarm.js';
import { loadAgentsFromDir } from '../src/loader.js';
import type { Agent } from '../src/types.js';

const __filename = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(__filename), '..');

// Load a small stable fixture set for tests
function getFixtureAgents(count = 3): Agent[] {
  const all = loadAgentsFromDir(REPO_ROOT);
  return all.slice(0, count);
}

// ---------------------------------------------------------------------------
// buildSwarm
// ---------------------------------------------------------------------------
describe('buildSwarm', () => {
  it('throws when given an empty agents array', () => {
    expect(() => buildSwarm([])).toThrow('buildSwarm requires at least one agent');
  });

  it('returns a swarm with the same agents array content', () => {
    const agents = getFixtureAgents(2);
    const swarm = buildSwarm(agents);
    expect(swarm.agents).toHaveLength(2);
    expect(swarm.agents[0]?.name).toBe(agents[0]?.name);
    expect(swarm.agents[1]?.name).toBe(agents[1]?.name);
  });

  it('orchestratorPrompt includes all agent names', () => {
    const agents = getFixtureAgents(3);
    const swarm = buildSwarm(agents);
    for (const a of agents) {
      expect(swarm.orchestratorPrompt).toContain(a.name);
    }
  });

  it('orchestratorPrompt includes agent descriptions', () => {
    const agents = getFixtureAgents(2);
    const swarm = buildSwarm(agents);
    for (const a of agents) {
      expect(swarm.orchestratorPrompt).toContain(a.description);
    }
  });

  it('orchestratorPrompt embeds system prompts in <system-prompt> tags', () => {
    const agents = getFixtureAgents(1);
    const swarm = buildSwarm(agents);
    expect(swarm.orchestratorPrompt).toContain('<system-prompt>');
    expect(swarm.orchestratorPrompt).toContain('</system-prompt>');
  });

  it('uses default swarm name when not provided', () => {
    const agents = getFixtureAgents(1);
    const swarm = buildSwarm(agents);
    expect(swarm.orchestratorPrompt).toContain('Agency Swarm');
  });

  it('uses custom swarm name when provided', () => {
    const agents = getFixtureAgents(1);
    const swarm = buildSwarm(agents, { name: 'MVP Squad' });
    expect(swarm.orchestratorPrompt).toContain('MVP Squad');
  });

  it('includes mission statement when provided', () => {
    const agents = getFixtureAgents(1);
    const swarm = buildSwarm(agents, { mission: 'Launch the product by Q4' });
    expect(swarm.orchestratorPrompt).toContain('Launch the product by Q4');
  });

  it('works with a single agent', () => {
    const [single] = getFixtureAgents(1);
    const swarm = buildSwarm([single!]);
    expect(swarm.agents).toHaveLength(1);
    expect(swarm.orchestratorPrompt).toBeTruthy();
  });

  it('works with a full swarm of 10 agents', () => {
    const agents = getFixtureAgents(10);
    const swarm = buildSwarm(agents, {
      name: 'Full Agency',
      mission: 'Deliver a complete SaaS product',
    });
    expect(swarm.agents).toHaveLength(10);
    expect(swarm.orchestratorPrompt).toContain('Full Agency');
  });
});
