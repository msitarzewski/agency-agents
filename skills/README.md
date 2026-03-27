# 🎯 Skills

**Skills** are the lightweight complement to Agents.

| | Agents | Skills |
|---|---|---|
| Tells Claude | Who to be | What to do |
| Format | Persona + process + examples | Direct instructions |
| Lines per file | 100–400 | 20–50 |
| Token cost | High (full persona loaded every request) | Low |
| Best for | Long sessions where personality consistency matters | One-shot tasks, high-frequency invocations |

**The insight**: Claude already has the domain expertise. It doesn't need a persona scaffold to review code well or write a good PRD — it needs focused instructions. Skills provide that at a fraction of the token cost.

---

## Using Skills with Claude Code

```bash
# Copy all skills to your Claude Code commands directory
cp -r skills/engineering skills/product skills/content \
      skills/sales skills/testing skills/design \
      ~/.claude/commands/

# Or install selectively
cp skills/engineering/code-review.md ~/.claude/commands/
```

Invoke in any Claude Code session:
```
/code-review
/debug
/architect
/prd
/outreach
```

---

## Skill Catalog

### 💻 Engineering

| Skill | What it does |
|---|---|
| [`code-review`](engineering/code-review.md) | Review changed files for bugs, security issues, maintainability |
| [`refactor`](engineering/refactor.md) | Refactor for clarity without changing behaviour |
| [`debug`](engineering/debug.md) | Systematic root-cause diagnosis and fix |
| [`architect`](engineering/architect.md) | Design system or feature architecture before coding |
| [`security-scan`](engineering/security-scan.md) | Audit for vulnerabilities across the attack surface |
| [`test-gen`](engineering/test-gen.md) | Generate tests for a function, module, or feature |
| [`perf-audit`](engineering/perf-audit.md) | Identify and fix performance bottlenecks |
| [`pr-description`](engineering/pr-description.md) | Write a clear, useful PR description from the diff |
| [`api-design`](engineering/api-design.md) | Design a clean, consistent API surface |
| [`tech-debt`](engineering/tech-debt.md) | Inventory and prioritise technical debt |
| [`incident`](engineering/incident.md) | Run incident response: triage, mitigate, document |

### 📋 Product

| Skill | What it does |
|---|---|
| [`prd`](product/prd.md) | Write a Product Requirements Document |
| [`user-story`](product/user-story.md) | Write user stories with testable acceptance criteria |
| [`sprint-plan`](product/sprint-plan.md) | Prioritise backlog and produce a committed sprint plan |

### ✍️ Content

| Skill | What it does |
|---|---|
| [`linkedin-post`](content/linkedin-post.md) | Write a LinkedIn post — direct, specific, no buzzwords |
| [`content-brief`](content/content-brief.md) | Write a content brief for any format |

### 💼 Sales

| Skill | What it does |
|---|---|
| [`outreach`](sales/outreach.md) | Write cold outreach copy (LinkedIn note, DM, email) |
| [`discovery`](sales/discovery.md) | Prepare for and run a discovery call |

### 🧪 Testing

| Skill | What it does |
|---|---|
| [`qa-plan`](testing/qa-plan.md) | Write a QA test plan for a feature or release |
| [`e2e-tests`](testing/e2e-tests.md) | Write end-to-end test scenarios and implementation |

### 🎨 Design

| Skill | What it does |
|---|---|
| [`ux-review`](design/ux-review.md) | Critique UI/UX for real usability issues |

---

## Skill File Format

```markdown
---
name: skill-name
description: One-line description of what this skill produces
---

# Skill Name

One-line purpose statement.

## Process
1. Numbered steps — what to do, not who to be.
2. Each step is specific and mechanically followable.

## Output
Exact format or template of what to produce.

## Rules
- Hard constraints that change behaviour (optional).
- Only include if removing this line would change the output.
```

### What makes a good skill

**Do:**
- Start with what the skill does, not what the model "is"
- Use numbered steps that can be followed mechanically
- Specify the exact output format
- Include only constraints that actually change behaviour

**Don't:**
- Add identity/persona sections (`You are an expert who...`)
- Add memory sections (`You remember patterns from previous work...`)
- Add communication style, emoji headers, or success metrics the model can't verify
- Duplicate instructions the model already follows by default

**The bar**: If removing a line doesn't change the output, remove it.

---

## Contributing Skills

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for the PR process. For skills specifically:

1. Skills live in `skills/<category>/skill-name.md`
2. Use the minimal frontmatter: `name` and `description` only
3. Target 20–50 lines per skill. If it needs more, split it into two skills
4. Test: invoke the skill on a real task. Does it produce the right output without the extra lines? Then the extra lines are waste — cut them
5. Add a row to the table in this README and open a PR
