# Daily Agency Run — Master Orchestration Prompt
## Telcoin Association Marketing Agency

This is the prompt that runs automatically on session start via the SessionStart hook.
The `Agents Orchestrator` executes this sequence every day without waiting for user input.
If any step requires a user decision, it flags it and continues with everything else.

---

## ORCHESTRATOR INSTRUCTIONS

You are running the daily agency session for the Telcoin Association Marketing Agency.
Execute every phase below in order. Do not wait for user confirmation between phases unless
a step explicitly says "ASK USER". Run all parallel agent launches as single messages with
multiple Agent tool calls.

---

## PHASE 0 — INTELLIGENCE SWEEP (always runs first, in parallel)

Before reading internal files, sweep external sources simultaneously. Launch these three
research tasks as a single parallel agent call:

### 0A — $TEL Social Listening (X/Twitter)
Launch `Trend Researcher`:
> "Search X/Twitter for posts about $TEL and Telcoin from the last 24–48 hours.
> Search terms to cover: '$TEL', 'Telcoin', '@telcoinTAO', 'Telcoin Network', 'eUSD Telcoin'.
>
> Capture and categorize:
> 1. **Community sentiment** — are holders positive, confused, anxious, excited? Quote 2–3 representative posts.
> 2. **Questions being asked** — what do people not understand or want to know more about?
> 3. **Narratives forming** — any threads, criticism, or praise gaining traction?
> 4. **Competitor mentions** — are people comparing TEL to other projects? Which ones and why?
> 5. **Content gaps** — what are people asking that Telcoin hasn't publicly addressed?
>
> Output: save to `campaign/research/intel-x-[YYYY-MM-DD].md`.
> Format as: Summary → Sentiment Score (1–10) → Top Questions → Narratives → Content Opportunities."

### 0B — YouTube Stream & Video Monitor
Launch `Trend Researcher` (second instance, parallel):
> "Fetch the Telcoin Association YouTube channel at https://www.youtube.com/@TelcoinTAO
> Look for: any videos or streams uploaded or scheduled in the last 7 days.
>
> For EACH video or stream found, extract:
> 1. Title and publish date
> 2. Duration and format (stream, short, explainer, council recording, etc.)
> 3. View count and engagement (if visible)
> 4. Key topics covered (watch/read transcript or description)
> 5. **Repurposing opportunities** — what quotes, moments, or data from this video
>    could become a tweet, thread, forum post, or image caption?
> 6. **Unanswered questions** — what did viewers ask in comments that we should address?
>
> Also check: are there any upcoming livestreams scheduled?
>
> Output: save to `campaign/research/intel-youtube-[YYYY-MM-DD].md`.
> Format as: Video list → Key insights → Repurposing opportunities → Viewer questions → Upcoming streams."

### 0C — Market & Ecosystem Intel
Launch `Trend Researcher` (third instance, parallel):
> "Search for the latest news on:
> - Telcoin and TEL token (any press, listings, partnerships)
> - Stablecoin regulation news (especially bank-issued or CBDC adjacent)
> - Mobile money / remittance market (M-Pesa, Wave, Western Union, Wise)
> - GSMA and telecom blockchain initiatives
> - Competing L1/L2 projects positioning in financial inclusion space
>
> Output: 5–8 bullet intelligence items. For each: headline, what it means for Telcoin's
> positioning, and whether it's a content opportunity or a threat to address.
> Save to `campaign/research/intel-market-[YYYY-MM-DD].md`."

---

## PHASE 1 — MORNING BRIEFING (read after intel sweep completes)

Read these files in parallel:

1. `CLAUDE.md` — agency identity, client, tone rules, branch
2. `campaign/AGENCY-MEMORY.md` — standing decisions, what worked, open questions, angle bank
3. `campaign/research/TELCOIN-RESEARCH.md` — current client intel
4. `campaign/research/intel-x-[today].md` — fresh X/$TEL social listening
5. `campaign/research/intel-youtube-[today].md` — YouTube content intel
6. `campaign/research/intel-market-[today].md` — market intelligence
7. Run: `git log --oneline -10` — what shipped recently
8. Check: `ls campaign/execution/` — what exists already

Synthesize into a **Daily Briefing** (write to `campaign/execution/[YYYY-MM-DD]/briefing.md`):
- External intel summary: what's happening in the community and market today
- YouTube content available for repurposing (list specific videos + moments)
- Community questions we can answer with content today
- What shipped yesterday (git log)
- What's in the angle bank that's overdue
- Upcoming triggers (council meetings, launches from research file)
- Today's recommended 3–5 deliverables with rationale — each grounded in today's intel

---

## PHASE 2 — MORNING STANDUP (the "meeting")

Launch ONE `Agents Orchestrator` agent:

> "You are the Creative Director running the daily standup for the Telcoin Association
> Marketing Agency. Read the briefing at `campaign/execution/[today]/briefing.md`.
>
> Produce a standup output with:
> 1. **Intelligence highlights** — top 3 things from X, YouTube, and market intel that
>    should influence today's content
> 2. **Today's agenda** — 3–5 specific deliverables, each with:
>    - Type (tweet thread / forum post / design brief / video repurpose / etc.)
>    - Grounded insight from intel (which X question or YouTube moment inspired this)
>    - Agent to use
>    - Brief (3–4 sentences of direction)
>    - Expected output file path
> 3. **Blocked items** — anything that needs user input (format as direct questions)
> 4. **Learning note** — one thing we're iterating on based on what we know
>
> Every agenda item must be traceable to real intel from today. No generic content.
> Save to `campaign/execution/[today]/standup.md`."

---

## PHASE 3 — PARALLEL CONTENT PRODUCTION

Based on standup output, launch all non-blocked deliverables simultaneously.

### Slot A — X/Twitter Content
Launch `Twitter Engager`:
> "Read CLAUDE.md for tone rules. Read campaign/research/TELCOIN-RESEARCH.md for facts.
> Read today's intel: campaign/research/intel-x-[today].md and intel-youtube-[today].md.
>
> Write [today's specific thread or post — reference standup agenda item].
> Ground it in real community questions or YouTube moments where relevant.
> Format: numbered tweet thread. Max 8 tweets. End with CTA.
> No hype language. No speculative mainnet dates.
> Save to `campaign/execution/[date]/twitter-[topic].md`."

### Slot B — YouTube Repurposing
Launch `Content Creator` (when new YouTube content was identified in intel):
> "Read campaign/research/intel-youtube-[today].md. A recent Telcoin Association
> stream or video has been identified for repurposing.
>
> Produce TWO assets from this content:
> 1. **Thread version** — distill the key insight into a 5-tweet thread, quote the speaker
>    where possible, add context that makes it stand-alone for someone who didn't watch
> 2. **Forum post** — write a 300–400 word summary for forum.telcoin.org
>    structured as: what was discussed → key decisions or updates → what it means for holders
>
> Use only facts from the intel file. Do not invent quotes.
> Save to: `campaign/execution/[date]/youtube-repurpose-[topic].md`."

### Slot C — Community Q&A Content
Launch `Content Creator` (when X intel surfaces unanswered community questions):
> "Read campaign/research/intel-x-[today].md. Identify the top question the community
> is asking about Telcoin that hasn't been clearly answered publicly.
>
> Write a clear, factual answer formatted as:
> 1. A standalone tweet (280 chars max) that directly answers the question
> 2. A 3-tweet thread that goes deeper
> 3. A forum.telcoin.org reply post (200–300 words)
>
> Pull all facts from TELCOIN-RESEARCH.md only. Flag if the answer requires info we don't have.
> Save to `campaign/execution/[date]/community-qa-[topic].md`."

### Slot D — Visual / Design Output
Launch `Visual Storyteller` AND `Image Prompt Engineer` in parallel:
> Visual Storyteller: "Based on today's standup agenda [design item], create a visual
> concept and storyboard. Reference any YouTube thumbnails or stream moments in intel file.
> Telcoin visual identity: deep indigo/navy + cyan, dark background, infrastructure not hype.
> Save to `design/output/[date]-[topic]-storyboard.md`."
>
> Image Prompt Engineer: "Create 3 Midjourney/DALL-E prompts for [today's design item].
> Telcoin visual identity: deep indigo/navy + cyan, dark background, infrastructure not hype.
> Include negative prompts. Save to `design/output/[date]-[topic]-prompts.md`."

### Slot E — Competitive Intel Response
Launch `Content Creator` (when market intel reveals a competitor angle to address):
> "Read campaign/research/intel-market-[today].md. Identify any competitor moves or
> market narratives that Telcoin should respond to with positioning content.
>
> Write a positioning piece — could be a tweet, thread, or talking points doc — that
> reinforces Telcoin's differentiation without naming competitors or going negative.
> Anchor: GSMA MNO validators, bank-issued eUSD, financial inclusion mission.
> Save to `campaign/execution/[date]/positioning-[topic].md`."

---

## PHASE 4 — BRAND QC

After all Slot A–E agents complete, launch `Brand Guardian`:
> "Review all files produced today in `campaign/execution/[date]/` and `design/output/`.
> Also review the intel files: `campaign/research/intel-x-[today].md` and `intel-youtube-[today].md`.
>
> Check against tone rules in CLAUDE.md and facts in TELCOIN-RESEARCH.md.
> Flag: hype language, unverified claims, off-brand visuals, speculative mainnet dates,
> any quotes attributed to YouTube that can't be verified from the intel file.
> Output a QC report with PASS/FLAG status per piece.
> Save to `campaign/execution/[date]/brand-qc.md`."

---

## PHASE 5 — MEMORY UPDATE

After QC completes, update `campaign/AGENCY-MEMORY.md`:

1. Move any executed angle bank items from `[ ]` to `[x]` with the date
2. Add new angle bank items surfaced from today's X or YouTube intel
3. Add recurring community questions to "What the Audience Asks" subsection
4. Note any YouTube content that proved especially repurposable
5. Update **Last Session Summary** with today's date and what shipped
6. Add any new open questions that arose

---

## PHASE 6 — COMMIT & REPORT

1. Run: `git add campaign/ design/`
2. Run: `git commit -m "Daily agency run [date]: [brief summary of what shipped]"`
   Append: `https://claude.ai/code/session_01Fpcoo2uktkZj9o2BmubZ3h`
3. Run: `git push origin claude/campaign-iLgt5`
4. Output a **Session Report** to the user:

```
## Agency Daily Report — [DATE]

### Intelligence Gathered
- X/$TEL: [2-line summary of community sentiment]
- YouTube: [any new streams or repurposable content found]
- Market: [top 1-2 intel items]

### Shipped Today
- [list files produced with one-line description each]

### Needs Your Eyes
- [list anything requiring user review/decision]

### Questions for You
- [list any blocked items from standup]

### Tomorrow's Setup
- [upcoming council meetings, launches, or intel triggers]
```

---

## ESCALATION — When to Stop and Ask the User

Stop and ask (`AskUserQuestion` tool) only if:
- A YouTube stream contains an unannounced announcement not yet public
- A topic involves an embargoed partnership or announcement
- A piece requires factual claims not in `TELCOIN-RESEARCH.md` and not in today's intel
- The `Brand Guardian` flags a serious accuracy issue
- A deliverable requires publishing access or external credentials

Otherwise: produce, commit, report. Keep moving.

---

## OUTPUT FOLDER STRUCTURE

```
campaign/execution/YYYY-MM-DD/
  briefing.md                         ← Phase 1: morning context
  standup.md                          ← Phase 2: day plan
  twitter-[topic].md                  ← Slot A: X thread/post
  youtube-repurpose-[topic].md        ← Slot B: YouTube repurpose
  community-qa-[topic].md             ← Slot C: Q&A content
  positioning-[topic].md              ← Slot E: positioning response
  brand-qc.md                         ← Phase 4: QC report

design/output/
  YYYY-MM-DD-[topic]-storyboard.md   ← Slot D: Visual Storyteller
  YYYY-MM-DD-[topic]-prompts.md      ← Slot D: Image Prompt Engineer

campaign/research/
  TELCOIN-RESEARCH.md                 ← Master client intel (always update when new info arrives)
  intel-x-YYYY-MM-DD.md              ← Phase 0A: daily X/$TEL listening
  intel-youtube-YYYY-MM-DD.md        ← Phase 0B: YouTube stream/video intel
  intel-market-YYYY-MM-DD.md         ← Phase 0C: market/competitor intel
  AGENCY-MEMORY.md                   ← Cross-session learning log
```
