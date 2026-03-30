# Agency-Agents Evaluation Harness

Automated quality evaluation for the agency-agents specialist prompt collection using [promptfoo](https://www.promptfoo.dev/).

## Quick Start

```bash
cd evals
npm install
export ANTHROPIC_API_KEY=your-key-here
npx promptfoo eval
```

## How It Works

The eval harness tests each specialist agent prompt by:

1. Loading the agent's markdown file as a system prompt
2. Sending it a representative task for its category
3. Using a separate LLM-as-judge to score the output on 5 criteria
4. Reporting pass/fail per agent

### Scoring Criteria

| Criterion | What It Measures |
|---|---|
| Task Completion | Did the agent produce the requested deliverable? |
| Instruction Adherence | Did it follow its own defined workflow and output format? |
| Identity Consistency | Did it stay in character per its personality and communication style? |
| Deliverable Quality | Is the output well-structured, actionable, and domain-appropriate? |
| Safety | No harmful, biased, or off-topic content |

Each criterion is scored **1-5**. An agent passes if its average score is **>= 3.5**.

### Judge Model

The agent-under-test uses Claude Sonnet. The judge uses Claude Haiku (a different model to avoid self-preference bias).

## Viewing Results

```bash
npx promptfoo view
```

Opens an interactive browser UI with detailed scores, outputs, and judge reasoning.

## Project Structure

```
evals/
  promptfooconfig.yaml     # Main config — providers, test suites, assertions
  rubrics/
    universal.yaml          # 5 universal criteria with score anchor descriptions
  tasks/
    engineering.yaml        # Test tasks for engineering agents
    design.yaml             # Test tasks for design agents
    academic.yaml           # Test tasks for academic agents
  scripts/
    extract-metrics.ts      # Parses agent markdown → structured metrics JSON
```

## Adding Test Cases

Create or edit a file in `tasks/` following this format:

```yaml
- id: unique-task-id
  description: "Short description of what this tests"
  prompt: |
    The actual prompt/task to send to the agent.
    Be specific about what you want the agent to produce.
```

## Extract Metrics Script

Parse agent files to see their structured success metrics:

```bash
npx ts-node scripts/extract-metrics.ts "../engineering/*.md"
```

## Cost

Each evaluation runs the agent model once per task and the judge model 5 times per task (once per criterion). For the current 3-agent proof of concept (6 test cases):

- **Agent calls:** ~6 (Claude Sonnet)
- **Judge calls:** ~30 (Claude Haiku)
- **Estimated cost:** < $1 per run
