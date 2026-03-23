# Cognetivy Integration

> Use Agency agents with [Cognetivy](https://cognetivy.com), the AI knowledge management and cognitive assistant platform.

## What Is Cognetivy?

Cognetivy is a platform for building AI-powered knowledge assistants and cognitive workflows. It supports custom agent personas, knowledge bases, and multi-step reasoning pipelines. Agency agents can be loaded as persona definitions to give Cognetivy assistants specialized expertise.

## How It Works

Cognetivy uses persona definitions to shape how its AI assistants behave. Agency agents map directly to this concept — each agent's identity, mission, rules, and deliverables become the persona that drives a Cognetivy assistant.

### Key Concepts

| Agency Concept | Cognetivy Equivalent |
|----------------|----------------------|
| Agent file (`.md`) | Persona definition |
| Identity & Memory | Persona context |
| Core Mission | Task instructions |
| Critical Rules | Guardrails / constraints |
| Technical Deliverables | Output templates |

## Setup

### 1. Choose Your Agents

Browse the [full agent roster](../../README.md) and pick agents relevant to your use case. Popular choices for knowledge workflows:

- **Code Reviewer** — code quality in knowledge-assisted dev workflows
- **Technical Writer** — documentation generation from knowledge bases
- **Software Architect** — architecture decision support
- **Compliance Auditor** — policy and regulatory checks
- **Workflow Architect** — process mapping and optimization

### 2. Import Agent as Persona

In the Cognetivy dashboard:

1. Navigate to **Personas** (or **Agents**, depending on your Cognetivy version)
2. Click **Create New Persona**
3. Copy the content of an Agency agent file (e.g., `engineering/engineering-code-reviewer.md`)
4. Paste it into the **System Prompt** or **Persona Definition** field
5. Configure the persona name and description from the agent's frontmatter
6. Save and attach the persona to your assistant or workflow

### 3. Attach Knowledge Base

Cognetivy's strength is connecting personas to knowledge bases. For best results:

```
Persona (Agency Agent)
    +
Knowledge Base (your docs, code, policies)
    =
Specialized assistant with domain context
```

Example configurations:

| Use Case | Agent | Knowledge Base |
|----------|-------|----------------|
| Code review assistant | Code Reviewer | Your codebase + style guides |
| Onboarding helper | Technical Writer | Internal docs + runbooks |
| Security advisor | Security Engineer | Security policies + CVE databases |
| Compliance checker | Compliance Auditor | Regulatory docs + internal policies |
| Architecture advisor | Software Architect | ADRs + system diagrams + tech radar |

### 4. Multi-Agent Workflows

Cognetivy supports multi-step pipelines where different personas handle different stages. Map this to Agency divisions:

```
Step 1: Software Architect → evaluates approach
Step 2: Senior Developer → implements solution
Step 3: Code Reviewer → reviews output
Step 4: Security Engineer → checks for vulnerabilities
```

Configure each step as a separate Cognetivy persona, each loaded with the corresponding Agency agent.

## Tips

- **Trim for context windows**: If your Cognetivy plan has limited context, use only the Identity, Core Mission, and Critical Rules sections of each agent. The deliverables section can be omitted for chat-style assistants.
- **Combine with RAG**: Agency agents work best in Cognetivy when paired with a relevant knowledge base via retrieval-augmented generation (RAG).
- **Version your personas**: Keep agent files in version control and update Cognetivy personas when you pull new versions from The Agency repo.
- **Test with real queries**: After importing an agent, test it with domain-specific questions to verify the persona behaves as expected.

## Example: Technical Writer Assistant

1. Import `engineering/engineering-technical-writer.md` as a Cognetivy persona
2. Attach your project's existing documentation as a knowledge base
3. Configure the assistant to help with:
   - Generating API reference from code
   - Writing onboarding guides
   - Reviewing docs for clarity and completeness
   - Maintaining a consistent documentation style

## Resources

- [Cognetivy Documentation](https://docs.cognetivy.com)
- [The Agency Agent Roster](../../README.md)
- [Contributing Guide](../../CONTRIBUTING.md)
