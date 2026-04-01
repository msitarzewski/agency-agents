// ---------------------------------------------------------------------------
// Pattern 3: Skill Discovery and Registry
// Dynamic capability map. Skills register, the orchestrator queries.
// Adding a skill requires zero changes to orchestration logic.
// ---------------------------------------------------------------------------

import type { Skill, SkillDefinition } from "../types/index.js";

export class SkillRegistry {
  private skills = new Map<string, Skill>();

  /** Register a skill. Overwrites if name already exists. */
  register(skill: Skill): void {
    this.skills.set(skill.name, skill);
  }

  /** Remove a skill by name. */
  unregister(name: string): void {
    this.skills.delete(name);
  }

  /** Get a skill by name. Returns undefined if not found. */
  get(name: string): Skill | undefined {
    return this.skills.get(name);
  }

  /** Check if a skill is registered. */
  has(name: string): boolean {
    return this.skills.has(name);
  }

  /** List all registered skill definitions (without exposing execute). */
  list(): SkillDefinition[] {
    return Array.from(this.skills.values()).map((s) => ({
      name: s.name,
      description: s.description,
      requiredTools: s.requiredTools,
      dependsOn: s.dependsOn,
      requiredPermission: s.requiredPermission,
    }));
  }

  /**
   * Find skills that can handle a given set of tool names. Useful for
   * the orchestrator to discover which skills are available given the
   * currently registered tools.
   */
  findByTools(availableTools: string[]): SkillDefinition[] {
    const available = new Set(availableTools);
    return this.list().filter((s) =>
      s.requiredTools.every((t) => available.has(t)),
    );
  }

  /**
   * Resolve the dependency graph for a skill. Returns the skill plus
   * all transitive dependencies in execution order.
   * Throws if a dependency is missing or circular.
   */
  resolve(name: string): Skill[] {
    const resolved: Skill[] = [];
    const seen = new Set<string>();

    const visit = (n: string, chain: string[]) => {
      if (seen.has(n)) return;
      if (chain.includes(n)) {
        throw new Error(`Circular skill dependency: ${chain.join(" → ")} → ${n}`);
      }

      const skill = this.skills.get(n);
      if (!skill) {
        throw new Error(`Skill "${n}" not found (required by ${chain.at(-1) ?? "root"})`);
      }

      for (const dep of skill.dependsOn) {
        visit(dep, [...chain, n]);
      }

      seen.add(n);
      resolved.push(skill);
    };

    visit(name, []);
    return resolved;
  }
}
