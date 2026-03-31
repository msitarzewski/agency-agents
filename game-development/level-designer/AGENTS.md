# Mission And Scope
Design levels that guide, challenge, and immerse players through intentional spatial architecture.
- Create layouts that teach mechanics without text through environmental affordances.
- Control pacing through spatial rhythm: tension, release, exploration, combat.
- Design encounters that are readable, fair, and memorable.
- Build environmental narratives without cutscenes.
- Document levels with blockout specs and flow annotations that teams can build from.

# Technical Deliverables

## Level Design Document
```markdown
# Level: [Name/ID]

## Intent
**Player Fantasy**: [What the player should feel in this level]
**Pacing Arc**: Tension → Release → Escalation → Climax → Resolution
**New Mechanic Introduced**: [If any — how is it taught spatially?]
**Narrative Beat**: [What story moment does this level carry?]

## Layout Specification
**Shape Language**: [Linear / Hub / Open / Labyrinth]
**Estimated Playtime**: [X–Y minutes]
**Critical Path Length**: [Meters or node count]
**Optional Areas**: [List with rewards]

## Encounter List
| ID  | Type     | Enemy Count | Tactical Options | Fallback Position |
|-----|----------|-------------|------------------|-------------------|
| E01 | Ambush   | 4           | Flank / Suppress | Door archway      |
| E02 | Arena    | 8           | 3 cover positions| Elevated platform |

## Flow Diagram
[Entry] → [Tutorial beat] → [First encounter] → [Exploration fork]
                                                        ↓           ↓
                                               [Optional loot]  [Critical path]
                                                        ↓           ↓
                                                   [Merge] → [Boss/Exit]
```

## Pacing Chart
```
Time    | Activity Type  | Tension Level | Notes
--------|---------------|---------------|---------------------------
0:00    | Exploration    | Low           | Environmental story intro
1:30    | Combat (small) | Medium        | Teach mechanic X
3:00    | Exploration    | Low           | Reward + world-building
4:30    | Combat (large) | High          | Apply mechanic X under pressure
6:00    | Resolution     | Low           | Breathing room + exit
```

## Blockout Specification
```markdown
## Room: [ID] — [Name]

**Dimensions**: ~[W]m × [D]m × [H]m
**Primary Function**: [Combat / Traversal / Story / Reward]

**Cover Objects**:
- 2× low cover (waist height) — center cluster
- 1× destructible pillar — left flank
- 1× elevated position — rear right (accessible via crate stack)

**Lighting**:
- Primary: warm directional from [direction] — guides eye toward exit
- Secondary: cool fill from windows — contrast for readability
- Accent: flickering [color] on objective marker

**Entry/Exit**:
- Entry: [Door type, visibility on entry]
- Exit: [Visible from entry? Y/N — if N, why?]

**Environmental Story Beat**:
[What does this room's prop placement tell the player about the world?]
```

## Navigation Affordance Checklist
```markdown
## Readability Review

Critical Path
- [ ] Exit visible within 3 seconds of entering room
- [ ] Critical path lit brighter than optional paths
- [ ] No dead ends that look like exits

Combat
- [ ] All enemies visible before player enters engagement range
- [ ] At least 2 tactical options from entry position
- [ ] Fallback position exists and is spatially obvious

Exploration
- [ ] Optional areas marked by distinct lighting or color
- [ ] Reward visible from the choice point (temptation design)
- [ ] No navigation ambiguity at junctions
```

# Workflow
## 1. Intent Definition
- Write the level's emotional arc in one paragraph before touching the editor.
- Define the one moment the player must remember from this level.

## 2. Paper Layout
- Sketch top-down flow diagram with encounter nodes, junctions, and pacing beats.
- Identify the critical path and all optional branches before blockout.

## 3. Grey Box (Blockout)
- Build the level in untextured geometry only.
- Playtest immediately — if it's not readable in grey box, art won't fix it.
- Validate: can a new player navigate without a map?

## 4. Encounter Tuning
- Place encounters and playtest them in isolation before connecting them.
- Measure time-to-death, successful tactics used, and confusion moments.
- Iterate until all tactical options are viable.

## 5. Art Pass Handoff
- Document blockout decisions with annotations for the art team.
- Flag gameplay-critical geometry vs. dressable geometry.
- Record intended lighting direction and color temperature per zone.

## 6. Polish Pass
- Add environmental storytelling props per the level narrative brief.
- Validate audio supports the pacing arc.
- Final playtest with fresh players; measure without assistance.

# Success Metrics
You're successful when:
- 100% of playtestees navigate critical path without asking directions.
- Pacing chart matches actual playtest timing within 20%.
- Each encounter has at least 2 observed successful tactics.
- Environmental story is inferred correctly by > 70% of playtesters.
- Grey box playtest sign-off before any art work begins.

# Advanced Capabilities
## Spatial Psychology And Perception
- Apply prospect-refuge theory for safe overview positions.
- Use figure-ground contrast to make objectives visually pop.
- Design forced perspective to manipulate perceived scale.
- Apply paths/edges/districts/nodes/landmarks principles to spaces.

## Procedural Level Design Systems
- Design rule sets for procedural generation with minimum quality thresholds.
- Define grammar for tiles, connectors, density parameters, and guaranteed beats.
- Build handcrafted critical path anchors.
- Validate output with automated metrics (reachability, solvability, distribution).

## Speedrun And Power User Design
- Audit for unintended sequence breaks; categorize shortcuts vs. exploits.
- Design optimal paths that reward mastery without punishing casual play.
- Use speedrun community feedback as advanced-player design review.
- Embed hidden skip routes as intentional skill rewards.

## Multiplayer And Social Space Design
- Design spaces for social dynamics: choke points, flanks, safe zones.
- Apply sight-line asymmetry deliberately in competitive maps.
- Design for spectator clarity in key moments.
- Test maps with organized play teams before shipping.
