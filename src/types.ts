/**
 * Core type definitions for agency-agents.
 */

/** Raw YAML frontmatter fields required in every agent `.md` file. */
export interface AgentFrontmatter {
  name: string;
  description: string;
  color: string;
}

/** Agent category identifiers matching the repository directory names. */
export type AgentCategory =
  | 'design'
  | 'engineering'
  | 'game-development'
  | 'marketing'
  | 'paid-media'
  | 'product'
  | 'project-management'
  | 'testing'
  | 'support'
  | 'spatial-computing'
  | 'specialized';

/** A fully-resolved agent with parsed frontmatter and body content. */
export interface Agent {
  /** Human-readable display name (from frontmatter). */
  name: string;
  /** URL-safe kebab-case identifier derived from `name`. */
  slug: string;
  /** One-line description of the agent's specialty (from frontmatter). */
  description: string;
  /** Accent colour hint for UI rendering (from frontmatter). */
  color: string;
  /** The directory category this agent belongs to. */
  category: AgentCategory;
  /** Absolute path to the source `.md` file. */
  filePath: string;
  /** Markdown body after the frontmatter block — the agent's system prompt. */
  systemPrompt: string;
}

/** A swarm groups multiple agents for coordinated execution. */
export interface Swarm {
  /** All resolved agents in this swarm. */
  agents: Agent[];
  /**
   * A ready-to-use orchestration system prompt that introduces each agent
   * and instructs an LLM on how to coordinate them.
   */
  orchestratorPrompt: string;
}

/** Options accepted by the swarm builder. */
export interface SwarmOptions {
  /**
   * Name of the swarm displayed in the orchestrator prompt.
   * @default "Agency Swarm"
   */
  name?: string;
  /**
   * High-level mission statement prepended to the orchestrator prompt.
   */
  mission?: string;
}


