# 🤝 Contributing to The Agency

First off, thank you for considering contributing to The Agency! It's people like you who make this collection of AI agents better for everyone.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Agent Design Guidelines](#agent-design-guidelines)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)
- [Community](#community)

---

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code:

- **Be Respectful**: Treat everyone with respect. Healthy debate is encouraged, but personal attacks are not tolerated.
- **Be Inclusive**: Welcome and support people of all backgrounds and identities.
- **Be Collaborative**: What we create together is better than what we create alone.
- **Be Professional**: Keep discussions focused on improving the agents and the community.

---

## 🎯 How Can I Contribute?

### 1. Create a New Agent

Have an idea for a specialized agent? Great! Here's how to add one:

1. **Fork the repository**
2. **Choose the appropriate division** — or propose a new one. Divisions are the
   top-level agent directories (e.g. `engineering/`, `security/`, `gis/`, `marketing/`,
   `finance/`…); browse them to find where your agent fits. The authoritative list —
   with labels, icons, and colors — is [`divisions.json`](divisions.json) at the repo
   root, so it's always current.

   > **Divisions are defined by `divisions.json`** (repo root) — the single source of
   > truth for the division set, validated in CI by `scripts/check-divisions.sh`.
   > **Proposing a new division** means: create the directory, add an entry to
   > `divisions.json` (label/icon/color), and add it to `AGENT_DIRS` in both
   > `scripts/convert.sh` and `scripts/lint-agents.sh`. The check fails the build
   > unless all of these agree and the directory contains at least one agent file.
   >
   > Note: `strategy/` (NEXUS playbooks/runbooks — no agent frontmatter) and
   > `integrations/` (generated per-tool output from `convert.sh`) are **not**
   > divisions and must never be added to the division lists.

3. **Create your agent file** following the template below
4. **Test your agent** in real scenarios
5. **Submit a Pull Request** with your agent

### 2. Improve Existing Agents

Found a way to make an agent better? Contributions welcome:

- Add real-world examples and use cases
- Enhance code samples with modern patterns
- Update workflows based on new best practices
- Add success metrics and benchmarks
- Fix typos, improve clarity, enhance documentation

### 3. Share Success Stories

Used these agents successfully? Share your story:

- Post in [GitHub Discussions](https://github.com/msitarzewski/agency-agents/discussions)
- Add a case study to the README
- Write a blog post and link it
- Create a video tutorial

### 4. Report Issues

Found a problem? Let us know:

- Check if the issue already exists
- Provide clear reproduction steps
- Include context about your use case
- Suggest potential solutions if you have ideas

---

## 🎨 Agent Design Guidelines

### Agent File Structure

Every agent should follow this structure:

```markdown
---
name: Agent Name
description: One-line description of the agent's specialty and focus
color: colorname or "#hexcode"
emoji: 🎯
vibe: One-line personality hook — what makes this agent memorable
services:                              # optional — only if the agent requires external services
  - name: Service Name
    url: https://service-url.com
    tier: free                         # free, freemium, or paid
---

# Agent Name

## 🧠 Your Identity & Memory
- **Role**: Clear role description
- **Personality**: Personality traits and communication style
- **Memory**: What the agent remembers and learns
- **Experience**: Domain expertise and perspective

## 🎯 Your Core Mission
- Primary responsibility 1 with clear deliverables
- Primary responsibility 2 with clear deliverables
- Primary responsibility 3 with clear deliverables
- **Default requirement**: Always-on best practices

## 🚨 Critical Rules You Must Follow
Domain-specific rules and constraints that define the agent's approach

## 📋 Your Technical Deliverables
Concrete examples of what the agent produces:
- Code samples
- Templates
- Frameworks
- Documents

## 🔄 Your Workflow Process
Step-by-step process the agent follows:
1. Phase 1: Discovery and research
2. Phase 2: Planning and strategy
3. Phase 3: Execution and implementation
4. Phase 4: Review and optimization

## 💭 Your Communication Style
- How the agent communicates
- Example phrases and patterns
- Tone and approach

## 🔄 Learning & Memory
What the agent learns from:
- Successful patterns
- Failed approaches
- User feedback
- Domain evolution

## 🎯 Your Success Metrics
Measurable outcomes:
- Quantitative metrics (with numbers)
- Qualitative indicators
- Performance benchmarks

## 🚀 Advanced Capabilities
Advanced techniques and approaches the agent masters
```

### Agent Structure

Agent files are organized into two semantic groups that map to
OpenClaw's workspace format and help other tools parse your agent:

#### Persona (who the agent is)
- **Identity & Memory** — role, personality, background
- **Communication Style** — tone, voice, approach
- **Critical Rules** — boundaries and constraints

#### Operations (what the agent does)
- **Core Mission** — primary responsibilities
- **Technical Deliverables** — concrete outputs and templates
- **Workflow Process** — step-by-step methodology
- **Success Metrics** — measurable outcomes
- **Advanced Capabilities** — specialized techniques

No special formatting is required — just keep persona-related sections
(identity, communication, rules) grouped separately from operational
sections (mission, deliverables, workflow, metrics). The `convert.sh`
script uses these section headers to automatically split agents into
tool-specific formats.

### Agent Design Principles

1. **🎭 Strong Personality**
   - Give the agent a distinct voice and character
   - Not "I am a helpful assistant" - be specific and memorable
   - Example: "I default to finding 3-5 issues and require visual proof" (Evidence Collector)

2. **📋 Clear Deliverables**
   - Provide concrete code examples
   - Include templates and frameworks
   - Show real outputs, not vague descriptions

3. **✅ Success Metrics**
   - Include specific, measurable metrics
   - Example: "Page load times under 3 seconds on 3G"
   - Example: "10,000+ combined karma across accounts"

4. **🔄 Proven Workflows**
   - Step-by-step processes
   - Real-world tested approaches
   - Not theoretical - battle-tested

5. **💡 Learning Memory**
   - What patterns the agent recognizes
   - How it improves over time
   - What it remembers between sessions

### External Services

Agents may depend on external services (APIs, platforms, SaaS tools) when
those services are essential to the agent's function. When they do:

1. **Declare dependencies** in frontmatter using the `services` field
2. **The agent must stand on its own** — strip the API calls and there
   should still be a useful persona, workflow, and expertise underneath
3. **Don't duplicate vendor docs** — reference them, don't reproduce them.
   The agent file should read like an agent, not a getting-started guide
4. **Prefer services with free tiers** so contributors can test the agent

The test: *is this agent for the user, or for the vendor?* An agent that
solves the user's problem using a service belongs here. A service's
quickstart guide wearing an agent costume does not.

### Tool-Specific Compatibility

**Qwen Code Compatibility**: Agent bodies support `${variable}` templating for dynamic context (e.g., `${project_name}`, `${task_description}`). Qwen SubAgents use minimal frontmatter: only `name` and `description` are required; `color`, `emoji`, and `version` fields are omitted as Qwen doesn't use them.

**Codex Compatibility**: Codex custom agents are generated as standalone TOML files. The Codex integration keeps a minimal 1:1 mapping: `name` and `description` are copied from frontmatter, and the Markdown body becomes `developer_instructions`. Source-only metadata such as `color`, `emoji`, `vibe`, and other unsupported frontmatter fields are omitted.

### Adding a Tool Integration

Want agency-agents to install into a new tool (a CLI, editor, or agent runtime)? First, **[open a Discussion](https://github.com/msitarzewski/agency-agents/discussions)** — new integration platforms are a "discuss first" change (see the PR Process below). Once there's alignment, a clean integration is small — usually **~5 files, never the converted output itself.** The just-merged Mistral Vibe integration is a good worked example to copy.

`tools.json` at the repo root is the single source of truth for the tool set, and `scripts/check-tools.sh` (CI) fails the build if any of the pieces below disagree. Run it — it names every place that must match.

**The checklist:**

1. **`tools.json`** — add an entry with `id`, `label`, `kebab`, `format`, `installKind`, `dest`, plus detect/version/scope and display fields. **Reuse an existing `format`** if your tool's rendered files are byte-identical to another's (e.g. tools that consume `SKILL.md` share `"format": "skill-md"` — no new renderer needed). Set `installKind` to `per-agent`, `roster`, or `plugin`. Set `icon` to `null` unless the [app](https://github.com/msitarzewski/agency-agents-app) ships a brand SVG for it.
2. **`scripts/convert.sh`** — add a `convert_<tool>()` (or reuse a shared `format` renderer) and wire it into the tool list + `--help`.
3. **`scripts/install.sh`** — add an `install_<tool>()` and register it in `ALL_TOOLS` + detection/labeling + `--help`.
4. **`.gitignore`** — add a rule for your tool's generated output under `integrations/<tool>/`. **This step is required and easy to miss.** Converted agent/skill files are generated locally by `convert.sh` and are **never committed** (see "Things we'll always close" below) — only `integrations/<tool>/README.md` is tracked. Match an existing per-tool entry.
5. **`integrations/<tool>/README.md`** — a short doc for the integration (every tool has one; it's the only committed file in the tool's directory).
6. **Run `./scripts/check-tools.sh`** — it must pass. It cross-checks `tools.json` against `install.sh` and `convert.sh` and flags anything missing.

If your PR commits the converted output (the generated `integrations/<tool>/*` files), CI and review will ask you to remove it and add the `.gitignore` rule instead.

### What Makes a Great Agent?

**Great agents have**:
- ✅ Narrow, deep specialization
- ✅ Distinct personality and voice
- ✅ Concrete code/template examples
- ✅ Measurable success metrics
- ✅ Step-by-step workflows
- ✅ Real-world testing and iteration

**Avoid**:
- ❌ Generic "helpful assistant" personality
- ❌ Vague "I will help you with..." descriptions
- ❌ No code examples or deliverables
- ❌ Overly broad scope (jack of all trades)
- ❌ Untested theoretical approaches

---

## 🔄 Pull Request Process

### What Belongs in a PR (and What Doesn't)

The fastest path to a merged PR is **one markdown file** — a new or improved agent. That's the sweet spot.

For anything beyond that, here's how we keep things smooth:

#### Always welcome as a PR
- Adding a new agent (one `.md` file)
- Improving an existing agent's content, examples, or personality
- Fixing typos or clarifying docs

#### Start a Discussion first
- New tooling, build systems, or CI workflows
- Architectural changes (new directories, new scripts, site generators)
- Changes that touch many files across the repo
- New integration formats or platforms

We love ambitious ideas — a [Discussion](https://github.com/msitarzewski/agency-agents/discussions) just gives the community a chance to align on approach before code gets written. It saves everyone time, especially yours.

#### Things we'll always close
- **Committed build output**: Generated files (`_site/`, compiled assets, converted agent files) should never be checked in. Users run `convert.sh` locally; its output is gitignored. When adding a new tool, adding that `.gitignore` rule is your step — see [Adding a Tool Integration](#adding-a-tool-integration).
- **PRs that bulk-modify existing agents** without a prior discussion — even well-intentioned reformatting can create merge conflicts for other contributors.
- **Near-duplicate "re-skins"**: New agents that are find-replace copies of an existing one (e.g. swapping a country or platform name) rather than genuinely new specialists. Run `scripts/check-agent-originality.sh` before submitting — CI runs it automatically.

### Before Submitting

1. **Test Your Agent**: Use it in real scenarios, iterate on feedback
2. **Follow the Template**: Match the structure of existing agents
3. **Add Examples**: Include at least 2-3 code/template examples
4. **Define Metrics**: Include specific, measurable success criteria
5. **Proofread**: Check for typos, formatting issues, clarity
6. **Check it's original**: Run `./scripts/check-agent-originality.sh path/to/your-agent.md`. It compares your agent against the whole roster and flags near-duplicates (a swapped country/platform name won't fool it). A new agent should be genuinely new — if you're localizing for a market, make the platforms, tactics, and examples actually different, not a find-replace.

### Submitting Your PR

1. **Fork** the repository
2. **Create a branch**: `git checkout -b add-agent-name`
3. **Make your changes**: Add your agent file(s)
4. **Commit**: `git commit -m "Add [Agent Name] specialist"`
5. **Push**: `git push origin add-agent-name`
6. **Open a Pull Request** with:
   - Clear title: "Add [Agent Name] - [Category]"
   - Description of what the agent does
   - Why this agent is needed (use case)
   - Any testing you've done

### PR Review Process

1. **Community Review**: Other contributors may provide feedback
2. **Iteration**: Address feedback and make improvements
3. **Approval**: Maintainers will approve when ready
4. **Merge**: Your contribution becomes part of The Agency!

### PR Template

```markdown
## Agent Information
**Agent Name**: [Name]
**Category**: [engineering/design/marketing/etc.]
**Specialty**: [One-line description]

## Motivation
[Why is this agent needed? What gap does it fill?]

## Testing
[How have you tested this agent? Real-world use cases?]

## Checklist
- [ ] Original — not a near-duplicate (ran `scripts/check-agent-originality.sh`)
- [ ] Follows agent template structure
- [ ] Includes personality and voice
- [ ] Has concrete code/template examples
- [ ] Defines success metrics
- [ ] Includes step-by-step workflow
- [ ] Proofread and formatted correctly
- [ ] Tested in real scenarios
```

---

## 📐 Style Guide

### Writing Style

- **Be specific**: "Reduce page load by 60%" not "Make it faster"
- **Be concrete**: "Create React components with TypeScript" not "Build UIs"
- **Be memorable**: Give agents personality, not generic corporate speak
- **Be practical**: Include real code, not pseudo-code

### Formatting

- Use **Markdown formatting** consistently
- Include **emojis** for section headers (makes scanning easier)
- Use **code blocks** for all code examples with proper syntax highlighting
- Use **tables** for comparing options or showing metrics
- Use **bold** for emphasis, `code` for technical terms

### Code Examples

```markdown
## Example Code Block

\`\`\`typescript
// Always include:
// 1. Language specification for syntax highlighting
// 2. Comments explaining key concepts
// 3. Real, runnable code (not pseudo-code)
// 4. Modern best practices

interface AgentExample {
  name: string;
  specialty: string;
  deliverables: string[];
}
\`\`\`
```

### Tone

- **Professional but approachable**: Not overly formal or casual
- **Confident but not arrogant**: "Here's the best approach" not "Maybe you could try..."
- **Helpful but not hand-holding**: Assume competence, provide depth
- **Personality-driven**: Each agent should have a unique voice

---

## 🌟 Recognition

Contributors who make significant contributions will be:

- Listed in the README acknowledgments section
- Highlighted in release notes
- Featured in "Agent of the Week" showcases (if applicable)
- Given credit in the agent file itself

---

## 🤔 Questions?

- **General Questions**: [GitHub Discussions](https://github.com/msitarzewski/agency-agents/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/msitarzewski/agency-agents/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/msitarzewski/agency-agents/issues)
- **Community Chat**: [Join our discussions](https://github.com/msitarzewski/agency-agents/discussions)

---

## 📚 Resources

### For New Contributors

- [README.md](README.md) - Overview and agent catalog
- [Example: Frontend Developer](engineering/engineering-frontend-developer.md) - Well-structured agent example
- [Example: Reddit Community Builder](marketing/marketing-reddit-community-builder.md) - Great personality example
- [Example: Whimsy Injector](design/design-whimsy-injector.md) - Creative specialist example

### For Agent Design

- Read existing agents for inspiration
- Study the patterns that work well
- Test your agents in real scenarios
- Iterate based on feedback

---

## 🎉 Thank You!

Your contributions make The Agency better for everyone. Whether you're:

- Adding a new agent
- Improving documentation
- Fixing bugs
- Sharing success stories
- Helping other contributors

**You're making a difference. Thank you!**

---

<div align="center">

**Questions? Ideas? Feedback?**

[Open an Issue](https://github.com/msitarzewski/agency-agents/issues) • [Start a Discussion](https://github.com/msitarzewski/agency-agents/discussions) • [Submit a PR](https://github.com/msitarzewski/agency-agents/pulls)

Made with ❤️ by the community

</div>
