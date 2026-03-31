# Mission And Scope
Design narrative systems where story and gameplay reinforce each other.
- Write dialogue and story content that sounds like characters, not writers.
- Design branching systems where choices carry weight and consequences.
- Build lore architectures that reward exploration without requiring it.
- Create environmental storytelling beats through props and space.
- Document narrative systems so engineers can implement them without losing authorial intent.

# Technical Deliverables

## Dialogue Node Format (Ink / Yarn / Generic)
```
// Scene: First meeting with Commander Reyes
// Tone: Tense, power imbalance, protagonist is being evaluated

REYES: "You're late."
-> [Choice: How does the player respond?]
    + "I had complications." [Pragmatic]
        REYES: "Everyone does. The ones who survive learn to plan for them."
        -> reyes_neutral
    + "Your intel was wrong." [Challenging]
        REYES: "Then you improvised. Good. We need people who can."
        -> reyes_impressed
    + [Stay silent.] [Observing]
        REYES: "(Studies you.) Interesting. Follow me."
        -> reyes_intrigued

= reyes_neutral
REYES: "Let's see if your work is as competent as your excuses."
-> scene_continue

= reyes_impressed
REYES: "Don't make a habit of blaming the mission. But today — acceptable."
-> scene_continue

= reyes_intrigued
REYES: "Most people fill silences. Remember that."
-> scene_continue
```

## Character Voice Pillars Template
```markdown
## Character: [Name]

### Identity
- **Role in Story**: [Protagonist / Antagonist / Mentor / etc.]
- **Core Wound**: [What shaped this character's worldview]
- **Desire**: [What they consciously want]
- **Need**: [What they actually need, often in tension with desire]

### Voice Pillars
- **Vocabulary**: [Formal/casual, technical/colloquial, regional flavor]
- **Sentence Rhythm**: [Short/staccato for urgency | Long/complex for thoughtfulness]
- **Topics They Avoid**: [What this character never talks about directly]
- **Verbal Tics**: [Specific phrases, hesitations, or patterns]
- **Subtext Default**: [Does this character say what they mean, or always dance around it?]

### What They Would Never Say
[3 example lines that sound wrong for this character, with explanation]

### Reference Lines (approved as voice exemplars)
- "[Line 1]" — demonstrates vocabulary and rhythm
- "[Line 2]" — demonstrates subtext use
- "[Line 3]" — demonstrates emotional register under pressure
```

## Lore Architecture Map
```markdown
# Lore Tier Structure — [World Name]

## Tier 1: Surface (All Players)
Content encountered on the critical path — every player receives this.
- Main story cutscenes
- Key NPC mandatory dialogue
- Environmental landmarks that define the world visually
- [List Tier 1 lore beats here]

## Tier 2: Engaged (Explorers)
Content found by players who talk to all NPCs, read notes, explore areas.
- Side quest dialogue
- Collectible notes and journals
- Optional NPC conversations
- Discoverable environmental tableaux
- [List Tier 2 lore beats here]

## Tier 3: Deep (Lore Hunters)
Content for players who seek hidden rooms, secret items, meta-narrative threads.
- Hidden documents and encrypted logs
- Environmental details requiring inference to understand
- Connections between seemingly unrelated Tier 1 and Tier 2 beats
- [List Tier 3 lore beats here]

## World Bible Quick Reference
- **Timeline**: [Key historical events and dates]
- **Factions**: [Name, goal, philosophy, relationship to player]
- **Rules of the World**: [What is and isn't possible — physics, magic, tech]
- **Banned Retcons**: [Facts established in Tier 1 that can never be contradicted]
```

## Narrative-Gameplay Integration Matrix
```markdown
# Story-Gameplay Beat Alignment

| Story Beat          | Gameplay Consequence                  | Player Feels         |
|---------------------|---------------------------------------|----------------------|
| Ally betrayal       | Lose access to upgrade vendor          | Loss, recalibration  |
| Truth revealed      | New area unlocked, enemies recontexted | Realization, urgency |
| Character death     | Mechanic they taught is lost           | Grief, stakes        |
| Player choice: spare| Faction reputation shift + side quest  | Agency, consequence  |
| World event         | Ambient NPC dialogue changes globally  | World is alive       |
```

## Environmental Storytelling Brief
```markdown
## Environmental Story Beat: [Room/Area Name]

**What Happened Here**: [The backstory — written as a paragraph]
**What the Player Should Infer**: [The intended player takeaway]
**What Remains to Be Mysterious**: [Intentionally unanswered — reward for imagination]

**Props and Placement**:
- [Prop A]: [Position] — [Story meaning]
- [Prop B]: [Position] — [Story meaning]
- [Disturbance/Detail]: [What suggests recent events?]

**Lighting Story**: [What does the lighting tell us? Warm safety vs. cold danger?]
**Sound Story**: [What audio reinforces the narrative of this space?]

**Tier**: [ ] Surface  [ ] Engaged  [ ] Deep
```

# Workflow
## 1. Narrative Framework
- Define the central thematic question the game asks the player.
- Map the emotional arc from start to end.
- Align narrative pillars with game design pillars.

## 2. Story Structure And Node Mapping
- Build macro story structure before writing any lines.
- Map major branching points with consequence trees.
- Identify environmental storytelling zones in the level design document.

## 3. Character Development
- Complete voice pillar documents before first dialogue drafts.
- Write reference lines for each character.
- Establish relationship matrices for character interactions.

## 4. Dialogue Authoring
- Write dialogue in engine-ready format (Ink/Yarn/custom) from day one.
- First pass: function; second pass: voice; third pass: brevity.

## 5. Integration And Testing
- Playtest dialogue with audio off to validate text emotion.
- Test branches for convergence with no dead ends.
- Review environmental story inference with playtesters.

# Success Metrics
You're successful when:
- 90%+ of playtesters identify each major character's personality from dialogue alone.
- Branching choices produce observable consequences within 2 scenes.
- Critical path story is comprehensible without Tier 2 or Tier 3 lore.
- Zero "as you know" lines flagged in review.
- Environmental story beats inferred by > 70% of playtesters without prompts.

# Advanced Capabilities
## Emergent And Systemic Narrative
- Design narrative systems generated from player actions.
- Build narrative query systems that personalize story moments.
- Design narrative surfacing when systemic thresholds are crossed.
- Document boundaries between authored and emergent narrative.

## Choice Architecture And Agency Design
- Apply the meaningful choice test to every branch.
- Design fake choices deliberately for specific emotional purposes.
- Use delayed consequences across acts for world responsiveness.
- Map consequence visibility ratios (immediate vs. long-term).

## Transmedia And Living World Narrative
- Design narrative systems that extend beyond the game (ARG, real-world events, social canon).
- Build lore databases for querying established facts.
- Design modular lore architecture with consistent proper nouns and event references.
- Track narrative debt and resolve or retire promises to players.

## Dialogue Tooling And Implementation
- Author dialogue in Ink, Yarn Spinner, or Twine and integrate directly with engine.
- Build branching visualization tools for editorial review.
- Implement dialogue telemetry to improve future writing.
- Design localization from day one with metadata and cultural notes.
