# Telcoin Association Content Operating System
## Distilled from: "TELCOIN ASSOCIATION CONTENT OPERATING SYSTEM" (assets/)
## Voice rules distilled from: "LLM Voice Principles" (assets/)
## Last updated: March 16, 2026

---

## Strategic Positioning

**What Telcoin Association is not competing on:**
- Hype-driven announcements
- Influencer partnerships
- Meme culture or viral content
- Price speculation narratives

**What we are:**
The credible governance institution. A Swiss nonprofit coordinating constitutional governance of blockchain infrastructure built for mobile network operators and financial inclusion.

**The brand book rule:** "The Telcoin Association does not chase engagement. It earns credibility."

This positioning speaks to: institutional investors, GSMA members evaluating validator participation, developers seeking stable governed infrastructure, community members seeking transparency, and regulators looking for examples of responsible crypto governance.

---

## Content System Architecture - The Four Layers

### Layer 1: Governance
- **Purpose**: Document council activity and governance decisions
- **Content types**: Meeting reminders, recaps, proposal alerts, vote announcements (image required)
- **Frequency**: Tied to actual council events
- **Flexibility**: Low
- **Tone**: Strictly institutional (Tier 1) - no emojis, no contractions, no enthusiasm language
- **CTAs**: Directional only - "Read the agenda", "Observe via Discord", "View the record"
- **No conversation prompts** unless directional

### Layer 2: Education
- **Purpose**: Build systematic understanding of the platform and governance system
- **Content types**: Explainers, concept introductions, process documentation (image required)
- **Frequency**: 2-4 posts per week depending on governance activity
- **Flexibility**: Medium - can compress or expand based on other layers
- **Tone**: Institutional but accessible (Tier 2)
- **Ends with**: One institutional conversation prompt (Neutral Authority)

### Layer 3: Milestone
- **Purpose**: Communicate major developments and announcements
- **Content types**: Announcements, explainer threads, progress updates (image required)
- **Frequency**: As events occur
- **Flexibility**: High - overrides other content when active
- **Priority posts**: Run the 60-minute launch window after publishing

### Layer 4: Community
- **Purpose**: Maintain connection with participants, acknowledge ecosystem activity
- **Content types**: Week in governance summaries, meeting reminders, participation invitations (image required)
- **Frequency**: 1-2 posts per week
- **Flexibility**: Medium - tied to meeting rhythm

---

## Weekly Post Volume by Week Type

| Week Type | Governance | Education | Milestone | Community | Total |
|---|---|---|---|---|---|
| Standard (council meetings, no major events) | 2-3 | 3-4 | - | 0-1 | 5-7 |
| Event (major milestone) | 1-2 | 0-2 | 3-5 | 1 | 5-8 |
| Quiet (no meetings scheduled) | - | 4-5 | - | 1-2 | 5-6 |

---

## X Distribution Overlay (applies to all layers)

### Conversation invitations (every non-Tier-1 post)
Every post except Tier 1 governance must include one conversation invitation. It must be:
- Institutional, not casual
- Not engagement bait
- "Neutral Authority" - no opinions, no personal voice, no emotional framing

**Good examples:**
- "What is your assessment?"
- "Which approach is preferable, and why?"
- "Which of these constitutional elements should be explained next: proposal types, council jurisdictions, or miner group representation?"

**Never:**
- "What do you think?"
- "Want to learn more?"
- "Drop your thoughts below"
- "Like if you agree"

### 60-minute launch window (priority posts only)
Priority post = Milestones, Votes, Key Education posts where correct interpretation and maximum distribution matters.

Procedure after publishing a priority post:
1. Monitor replies for the first 60 minutes
2. Answer early questions with substantive replies
3. Add clarifying context if the post is being misread
4. Keep the thread active with on-topic responses
5. Purpose: algorithm pickup happens in the first hour - active threads get out-of-network distribution

This does NOT change the tone of the post. It changes how you handle the first hour after posting.

### Link handling
- Default: Lead with insight first, include the link after the substantive content
- Never open a post with a URL - the link is supplementary, not the lead
- Exception: first-reply link placement is allowed for tested formats (threads) where analytics show improved performance

### Engagement bait avoidance
No giveaways, "tag 3 friends", "like if you agree" patterns. These trigger negative algorithmic signals.

---

## Image Production Workflow

Every @telcoinTAO post requires an accompanying image. No exceptions, across all four layers and all tiers.

### Skill selection

| Post type | Skill to use |
|---|---|
| Single tweet | `/tweet-card-brief` - generates a Figma-ready design brief for one card |
| Thread (2+ tweets) | `/thread-visual-pack` - generates a coordinated visual pack: header card + 2-3 insert card briefs + AI image prompts for the full thread |
| AI-generated visual element needed | `/brand-image-prompt` - generates 3 Midjourney/Flux/DALL-E prompt variants (dark, abstract, human-focused) for a specific topic |

These skills are complementary. `/tweet-card-brief` and `/thread-visual-pack` produce the full design brief; both reference `/brand-image-prompt` output when an AI-generated visual is part of the card.

### Production pipeline

1. **Generate tweet text** - draft the post(s) per Content OS rules
2. **Generate image brief alongside** - run the appropriate skill in parallel with or immediately after writing the tweet; do not treat image production as a separate step
3. **Composite in Figma** - import AI-generated visual (if used) as background layer; apply glass panel overlay; place typography in New Hero; add logo and hexagon motif per brand template
4. **Publish together** - tweet text and image go out as a unit; do not queue text without a corresponding image ready

Image briefs are saved alongside tweet drafts in the same `campaign/execution/[date]/` folder.

### Tier-based image guidance

**Tier 1 - Governance**: Type-only card or minimal dark card. No decorative illustration. Background: TEL Black #090920. Headline only, no supporting graphic element. Hexagon motif at very low opacity (8%) is acceptable. No AI-generated imagery.

**Tier 2 - Education**: Concept visual, architecture diagram, or abstract illustration tied to the topic. Richer visual treatment allowed. AI-generated imagery appropriate. Diagrams preferred when explaining a system or process (e.g., council hierarchy, token flow, validator structure).

**Tier 3 - Milestone**: Bold announcement card. High contrast, strong visual presence. AI-generated imagery or a purpose-built graphic. Proud but controlled - no hype imagery (no upward arrows, rockets, confetti). The visual should communicate institutional significance, not excitement.

**Tier 4 - Community**: Warmer treatment. Human element allowed where relevant - real-world contexts, people in genuine use scenarios. Still institutional; warmth is a register shift, not a visual style departure.

### Brand parameters (apply to every image produced)

| Parameter | Rule |
|---|---|
| Primary background | TEL Black #090920 (dark templates) or TEL White #F1F4FF (light templates) |
| Primary accent | Tel Royal Blue #3642B2 |
| Highlight | TEL Blue #14C8FF |
| Typography | New Hero Bold for headlines; New Hero Regular for body; placed in Figma post-production |
| No text in AI-generated images | All text is placed in Figma after image generation - never prompt AI tools to render text |
| Logo placement | Horizontal version, top-left, 1 mark height from top, 1.5 mark widths from left edge |
| Geometric motif | Hexagons - the brand signature shape; present on all cards |
| Prohibited imagery | Rockets, moons, upward arrows, confetti, explosions, neon/meme aesthetic, stock photo corporate blandness |

---

## Learning Path System

Rather than weekly themes, education content follows sequential learning paths. Posts are distributed into available slots after governance content is scheduled.

### LP1: Governance Fundamentals
- Purpose: Establish baseline understanding of what Telcoin Association is and how governance works
- Completion target: 4-5 weeks
- Status: **Complete** (published Feb 9 through ~Mar 8, 2026)
- Posts: What is TA? / Swiss Verein / Constitution / Four Miner Groups / Miner Councils / Platform Council

### LP2: Platform Architecture
- Purpose: Explain what the Telcoin Platform is and how it functions
- Completion target: 3-4 weeks
- Status: **In progress** (Mar 9, 2026 -)
- Posts: Platform Overview (done) / Telcoin Network (done) / TELx (done) / eUSD + TDAB (pending) / Telcoin Wallet (pending) / Integration story (pending)

### LP3: Differentiation
- Purpose: Position Telcoin Association's model against alternatives and explain why it matters
- Completion target: 3 weeks
- Status: **Not started**

### LP4: Participation
- Purpose: Guide prospective and existing participants on how to engage
- Completion target: 3 weeks
- Status: **Not started**

**Distribution rules:**
- Education posts fill available slots after governance content is scheduled
- Minimum 2 education posts per week, maximum 5
- Posts follow learning path sequence - LP1 completes before LP2 begins, etc.
- Each education post must end with one institutional conversation prompt
- Lead with insight, then include link (or link in follow-up reply)

---

## Brand Compliance Checklist (apply to every post before publishing)

**Language:**
- American English spelling
- Proper grammar and punctuation
- Oxford comma used
- No ALL CAPS
- No slang, memes, or internet language
- No contractions in Tier 1 governance content
- "Telcoin Association" not "Telcoin"
- "Telcoin Wallet" not "Telcoin App"
- En dashes ( - ) in body text; never em dashes

**Emoji rules:**
- Never in governance, regulatory, or financial updates (Tier 1)
- Maximum 1-2 in community or congratulatory posts (Tier 4)
- Never at the beginning of a post
- Neutral emojis only, yellow skin tone

**Hashtag rules:**
- Never in body text
- At end only if used
- Maximum 1-2
- Event-related only

**Tone by tier:**
- Tier 1 (Governance): Strictly institutional, no emojis, no enthusiasm, directional CTAs only
- Tier 2 (Education): Informative and factual, one conversation prompt at end
- Tier 3 (Milestone): Proud but controlled - not "excited" or "thrilled"
- Tier 4 (Community): Respectful, minimal warmth allowed

**CTA rules:**
- Clear, polite, non-promotional
- No "Don't miss out" or "Act now"
- No sales-style urgency
- Tier 1 only: "Read the agenda", "View the record", "Access the documentation", "Observe via Discord"

**Final check questions:**
- Would this sound appropriate in a regulatory newsletter?
- Does every claim rely on verifiable facts?
- Could this be misread as promotional or speculative?
- Does this clearly distinguish Telcoin Association from Telcoin?

---

## Voice Anti-Patterns (from LLM Voice Principles)

### The five bad instincts - internalize these
1. **Don't perform the conversation - have it.** If you're impressed, it shows in what you say next. Don't compliment the topic before addressing it.
2. **Match the stakes.** A simple governance update is not a revelation. Don't inflate it.
3. **Have a position.** State it. Don't both-sides. Don't land on a safe middle. A council decision has implications - say what they are.
4. **Earn your emphasis.** If everything is important, nothing is. Let the substance carry weight, not rhetorical decoration.
5. **Say it once, then move.** No restating what the reader just read. No padding. No transitions.

### Specific anti-patterns - never use these
**False drama:**
- "It's not just X - it's Y" (fake reframing)
- "Here's the thing" / "Here's where it gets interesting" / "And the best part?"
- "This is huge" / "This changes everything"
- "Buckle up" / "Strap in"
- "Let's be clear" / "Make no mistake"

**Buzzword soup:**
- "ecosystem" (when used as vague filler rather than describing something specific)
- "leverage" (as a verb)
- "robust" / "holistic" / "synergy" / "paradigm shift"
- "navigate" (when not literally navigating)
- "dive deep" / "unpack" / "landscape"

**Structural tics:**
- Starting paragraphs with "Now," or "So," or "Look,"
- Bullet-pointing things that should be a sentence
- Summarizing what the reader just read before responding
- Ending with unsolicited expansion offers ("Want me to turn this into a thread?")
- Thesis-antithesis-synthesis structure ending in a safe middle

**Negation-forward framing:**
- "Not just a governance body, but..." - just say what it is

### The test
Before producing any output, ask: would a real institutional communications director write this, or does it sound generated? If it sounds generated, rewrite it.

---

## Council Meeting Rhythm

Based on fortnightly (every two weeks) schedule:
- Meeting reminder: approximately 6 hours before the meeting
- Meeting recap: next day

**Active councils:**
- Platform and Treasury Council: fortnightly, Thursdays 4PM EST
- TAN Council: fortnightly, Thursdays 5PM EST
- TELx Council: fortnightly, Wednesdays 3PM EST (note: DST may affect calendar display)

---

## Production Cycle

**Inputs to provide for content generation:**
- Calendar: which council meetings are scheduled
- Education queue: next posts in current learning path
- Recent activity: meeting notes from prior week, proposals submitted
- Milestone status: any updates on Telcoin Network or other developments

**AI generates:**
- All draft posts for the week
- Rationale for each post
- Source references for factual claims
- Suggested link placements
- Compliance flag if any content is uncertain
- Proposed conversation prompt (Neutral Authority) for each post
- Link framing variant (in-body vs. follow-up reply)

**TAO reviews:**
- Factual accuracy
- Brand compliance
- Timing appropriateness
- Link correctness
- Whether the conversation prompt stays institutional

---

## Milestone: Telcoin Network Launch

Pre-launch content strategy:
- Continue LP2 education content on Telcoin Network architecture (evergreen, no date dependency)
- Progress updates are factual: "authorization process continues", not promissory
- No specific dates committed in content until confirmed by TA leadership

Launch week: all four core posts (announcement, technical explainer, validator status, what comes next) are Priority Posts and must use the 60-minute launch window procedure.

Post-launch: weekly or biweekly network status updates; education content shifts to "Telcoin Network in practice" topics.

---

## Weekly Approval Process

The weekly approval cycle runs every Wednesday via `/weekly-tweet-approval`. Running it on another day is permitted but note that the output file will flag the timing deviation.

### How the skill works

`/weekly-tweet-approval` launches four agents in parallel before writing anything:

- **Analytics Reporter** - reviews `campaign/execution/` for the prior 7 days; returns a 4-line summary: top post, bottom post, format insight, one recommendation. If no analytics data exists, defaults to Content OS baseline.
- **Sprint Prioritizer** - reads the research file, this document, and the Current Campaign Status section of `CLAUDE.md`; determines the next learning path post, upcoming governance events, and any milestone triggers; outputs a proposed 7-post content mix with day, time, type, topic, and structural rationale for each slot.
- **Twitter Engager** - drafts the complete tweet text for every post in the proposed mix, applying all tone and style rules; no invented stats.
- **Image Prompt Engineer** - generates a Midjourney/Flux/DALL-E prompt for the accompanying image for each post in the mix; single tweet posts get one 1200x675px prompt; thread posts get a header prompt plus one insert prompt per 2-3 tweets.

All four agents complete before the approval document is assembled.

### Output

The approval document is saved to `campaign/execution/[week-start-date]/WEEKLY-APPROVAL.md`.

It contains:
- **Schedule at a Glance** - a table of all posts for the week with day, time, layer, format, topic, and an approval checkbox per row. This is the bulk sign-off mechanism.
- **Structural Rationale** - 2-3 sentences on the week's overall content logic, one sentence on any analytics adjustment, one sentence on timing choices.
- **Individual post blocks** - full tweet text, image prompt, tier, format, rationale, 60-min launch window flag, and a three-option decision field (APPROVE / EDIT / SKIP) for post-level edits.
- **Bulk Approval line** - sign once to approve all posts as written.
- **Analytics Tracking table** - filled in after publishing; feeds the following Wednesday's performance signal.

### Approval workflow

1. The skill prints the Schedule at a Glance table directly in the chat response for a fast scan without opening the file.
2. To approve all posts as written, sign the Bulk Approval line in the file.
3. To edit individual posts, mark EDIT on the relevant row in the schedule table and add a note in that post's decision field.
4. To remove a post from the week, mark SKIP.
5. Return the marked-up file or relay decisions in chat.

The file is the approval mechanism. The skill does not request approval in the chat response.
