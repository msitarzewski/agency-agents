import type { Agent, Swarm, SwarmOptions } from './types.js';

/**
 * Build a {@link Swarm} from an array of resolved agents.
 *
 * The returned `orchestratorPrompt` is a self-contained system prompt that
 * introduces each agent's role and provides coordination instructions suitable
 * for passing to any LLM orchestrator.
 *
 * @example
 *   const swarm = buildSwarm([frontendAgent, backendAgent], {
 *     name: 'MVP Team',
 *     mission: 'Build a SaaS MVP in 4 weeks',
 *   });
 *   // swarm.orchestratorPrompt  →  feed to your LLM as system prompt
 */
export function buildSwarm(agents: Agent[], options: SwarmOptions = {}): Swarm {
  if (agents.length === 0) {
    throw new Error('buildSwarm requires at least one agent.');
  }

  const swarmName = options.name ?? 'Agency Swarm';
  const mission = options.mission ?? '';

  const agentSummaries = agents
    .map((a) => `### ${a.name} (${a.category})\n> ${a.description}`)
    .join('\n\n');

  const agentNames = agents.map((a) => a.name).join(', ');

  const orchestratorPrompt = [
    `# ${swarmName}`,
    '',
    mission ? `**Mission**: ${mission}\n` : '',
    `You are coordinating a swarm of ${agents.length} specialist AI agents: ${agentNames}.`,
    '',
    '## Agent Roster',
    '',
    agentSummaries,
    '',
    '## Coordination Rules',
    '',
    '1. **Assign tasks** to the most qualified agent based on their specialty.',
    '2. **Handoff context** clearly between agents — include relevant prior outputs.',
    '3. **One agent per task**: avoid overlapping responsibilities.',
    '4. **Quality gates**: each agent output must be reviewed before advancing.',
    '5. **Escalate blockers** immediately rather than stalling the pipeline.',
    '',
    '## Agent System Prompts',
    '',
    ...agents.map(
      (a) =>
        `### ${a.name}\n\n<system-prompt>\n${a.systemPrompt}\n</system-prompt>`,
    ),
  ]
    .join('\n')
    .trim();

  return { agents, orchestratorPrompt };
}
