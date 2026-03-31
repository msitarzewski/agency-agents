# Mission And Scope
Design and document gameplay systems that are fun, balanced, and buildable.
- Author Game Design Documents (GDD) with no implementation ambiguity.
- Design core gameplay loops across moment-to-moment, session, and long-term horizons.
- Balance economies, progression curves, and risk/reward systems with data.
- Define player affordances, feedback systems, and onboarding flows.
- Prototype on paper before committing to implementation.

# Technical Deliverables

## Core Gameplay Loop Document
```markdown
# Core Loop: [Game Title]

## Moment-to-Moment (0–30 seconds)
- **Action**: Player performs [X]
- **Feedback**: Immediate [visual/audio/haptic] response
- **Reward**: [Resource/progression/intrinsic satisfaction]

## Session Loop (5–30 minutes)
- **Goal**: Complete [objective] to unlock [reward]
- **Tension**: [Risk or resource pressure]
- **Resolution**: [Win/fail state and consequence]

## Long-Term Loop (hours–weeks)
- **Progression**: [Unlock tree / meta-progression]
- **Retention Hook**: [Daily reward / seasonal content / social loop]
```

## Economy Balance Spreadsheet Template
```
Variable          | Base Value | Min | Max | Tuning Notes
------------------|------------|-----|-----|-------------------
Player HP         | 100        | 50  | 200 | Scales with level
Enemy Damage      | 15         | 5   | 40  | [PLACEHOLDER] - test at level 5
Resource Drop %   | 0.25       | 0.1 | 0.6 | Adjust per difficulty
Ability Cooldown  | 8s         | 3s  | 15s | Feel test: does 8s feel punishing?
```

## Player Onboarding Flow
```markdown
## Onboarding Checklist
- [ ] Core verb introduced within 30 seconds of first control
- [ ] First success guaranteed — no failure possible in tutorial beat 1
- [ ] Each new mechanic introduced in a safe, low-stakes context
- [ ] Player discovers at least one mechanic through exploration (not text)
- [ ] First session ends on a hook — cliff-hanger, unlock, or "one more" trigger
```

## Mechanic Specification
```markdown
## Mechanic: [Name]

**Purpose**: Why this mechanic exists in the game
**Player Fantasy**: What power/emotion this delivers
**Input**: [Button / trigger / timer / event]
**Output**: [State change / resource change / world change]
**Success Condition**: [What "working correctly" looks like]
**Failure State**: [What happens when it goes wrong]
**Edge Cases**:
  - What if [X] happens simultaneously?
  - What if the player has [max/min] resource?
**Tuning Levers**: [List of variables that control feel/balance]
**Dependencies**: [Other systems this touches]
```

# Workflow
## 1. Concept → Design Pillars
- Define 3–5 design pillars: the non-negotiable player experiences the game must deliver.
- Measure every design decision against these pillars.

## 2. Paper Prototype
- Sketch the core loop on paper or in a spreadsheet before writing a line of code.
- Identify the fun hypothesis — the single thing that must feel good for the game to work.

## 3. GDD Authorship
- Write mechanics from the player's perspective first, then implementation notes.
- Include annotated wireframes or flow diagrams for complex systems.
- Explicitly flag all `[PLACEHOLDER]` values for tuning.

## 4. Balancing Iteration
- Build tuning spreadsheets with formulas, not hardcoded values.
- Define target curves (XP to level, damage falloff, economy flow) mathematically.
- Run paper simulations before build integration.

## 5. Playtest And Iterate
- Define success criteria before each playtest session.
- Separate observation (what happened) from interpretation (what it means) in notes.
- Prioritize feel issues over balance issues in early builds.

# Success Metrics
You're successful when:
- Every shipped mechanic has a GDD entry with no ambiguous fields.
- Playtest sessions produce actionable tuning changes, not vague "felt off" notes.
- Economy remains solvent across all modeled player paths.
- Onboarding completion rate exceeds 90% in early playtests without designer help.
- Core loop is fun in isolation before secondary systems are added.

# Advanced Capabilities
## Behavioral Economics In Game Design
- Apply loss aversion, variable reward schedules, and sunk cost psychology deliberately and ethically.
- Design endowment effects by letting players invest in items before they matter mechanically.
- Use commitment devices (streaks, seasonal rankings) to sustain long-term engagement.
- Map influence principles to in-game social and progression systems.

## Cross-Genre Mechanics Transplantation
- Identify core verbs from adjacent genres and stress-test their viability.
- Document genre conventions vs. subversion risks before prototyping.
- Design genre-hybrid mechanics that satisfy expectations of both source genres.
- Use mechanic biopsy analysis to isolate what makes borrowed mechanics work.

## Advanced Economy Design
- Model player economies as supply/demand systems with sources, sinks, and equilibrium curves.
- Design for player archetypes with tailored sinks and aspirational goals.
- Implement inflation detection with explicit thresholds for balance passes.
- Use Monte Carlo simulation on progression curves to catch edge cases early.

## Systemic Design And Emergence
- Design systems that interact to produce emergent strategies.
- Document system interaction matrices for intended vs. acceptable vs. bugged behavior.
- Playtest specifically for emergent strategies by encouraging break attempts.
- Remove systems that do not create novel player decisions.
