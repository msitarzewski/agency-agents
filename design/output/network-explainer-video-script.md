# Telcoin Network Architecture — Animated Explainer Video
## Full Motion Script + Storyboard
**Working title**: "How the Telcoin Network Actually Works"
**Target duration**: 105 seconds
**Format**: 16:9 primary (YouTube / X) | 9:16 cut notes per scene (TikTok / Reels)
**Style**: Dark-mode motion graphics — no live action, no 3D renders
**Tone**: Calm, authoritative narrator. Technical but accessible. Not hype, not academic.
**Authored**: March 12, 2026 | Telcoin Association Marketing Agency — Visual Storyteller

---

## COLOR PALETTE REFERENCE (motion designer use)

| Token | Hex | Usage |
|---|---|---|
| Deep navy background | `#0A0E1A` | Canvas base |
| Layer card background | `#0D1526` | Panel fills |
| TEL Blue | `#0047FF` | Primary accent, glows, borders |
| White | `#FFFFFF` | Primary text, icons |
| Steel blue | `#8BA3C9` | Secondary text, labels |
| Gold | `#C9A227` | Callout highlights (Rust stat, flywheel) |
| EVM layer card | `#1A2744` | Execution layer panel fill |

**Typography**: Inter or Neue Haas Grotesk — medium and regular weights only. Monospace (JetBrains Mono or IBM Plex Mono) for protocol stack labels only.

---

## SCENE-BY-SCENE SCRIPT

---

### SCENE 1 — HOOK
**Duration**: 8 seconds
**Cumulative timecode**: 0:00 – 0:08

---

**VISUAL**:
Cold open. Pure black — no title card, no logo. Hold for 12 frames (0.5s).

A single glowing blue dot materializes in screen center. `#0047FF`, soft radial bloom, 40px diameter. Radius of the bloom pulses once — contracts back to the dot. Pause 6 frames.

The dot begins to multiply: 6 more dots appear at irregular positions across a dark navy canvas (`#0A0E1A`). Thin, faint blue lines connect them, drawing in at ~200px/s. This is a sparse, abstract DAG-like graph. Nodes glow softly. Lines are 1px, 40% opacity white.

Then — a hard CUT. The graph disappears instantly. Full black frame for 4 frames. White sans-serif text types in from left, character by character, in a monospace font:

```
Most blockchains solve one problem.
Telcoin Network solves two.
```

Text size: 28px. Letter spacing: 0.04em. The cursor blinks once after the second line, then freezes. Hold 1.5 seconds.

**Color beat**: Black → deep navy (as graph builds) → black (cut) → black with white text.

**VO**: *(silence through the graph build — 3.5 seconds of no narration, letting the visual breathe)*
"Most blockchains solve one problem. Telcoin Network was built to solve two."

**ON-SCREEN TEXT**:
```
Most blockchains solve one problem.
Telcoin Network solves two.
```
*(No logo, no URL — nothing else)*

**TRANSITION**: Cut to black for 2 frames, then the background fades up to `#0A0E1A` deep navy as Scene 2 begins.

**VERTICAL CUT NOTE**: Center-crop the dot graph to 9:16 — graph nodes appear in a vertical column arrangement rather than horizontal spread. The monospace text fits naturally in 9:16 at 22px. No layout changes required.

---

### SCENE 2 — THE TWO-LAYER ARCHITECTURE
**Duration**: 14 seconds
**Cumulative timecode**: 0:08 – 0:22

---

**VISUAL**:
Open on the full `#0A0E1A` canvas. Centered in frame, two rectangular panels build in vertically from the canvas center — one rises up, one drops down, as if splitting apart from a single central line.

**Top panel** (Consensus Layer):
- Fills the upper half of screen center (roughly 55% canvas width, 34% canvas height)
- Background: `#0047FF` at 15% opacity
- Border: `#0047FF` solid, 1.5px
- Blue corner glow on all four corners — subtle, 30px radius
- Animates in with a smooth ease-out deceleration over 0.4s

**Bottom panel** (Execution Layer):
- Fills the lower half of screen center, same width
- Background: `#1A2744`
- Border: white at 40% opacity, 1px
- Animates in simultaneously with top panel, dropping from center to its final position

A downward-pointing chevron icon in `#0047FF` appears between the two panels as a connector element — it pulses once with a brief glow.

After both panels settle (0.4s after animation completes), text fades in inside each panel:

**Top panel text**:
- Small all-caps label: "CONSENSUS LAYER" (`#8BA3C9`, 11px, letter-spacing 0.12em)
- Main label: "Narwhal + Bullshark" (white, 22px, medium weight)
- Below: "DAG-Based Consensus" (`#8BA3C9`, 13px)

**Bottom panel text**:
- Small all-caps label: "EXECUTION LAYER" (`#8BA3C9`, 11px, letter-spacing 0.12em)
- Main label: "EVM-Compatible" (white, 22px, medium weight)
- Below: "Ethereum-standard execution" (`#8BA3C9`, 13px)

Both text groups fade in with a 0.2s opacity ease-in — no slide, no bounce, just clean fade.

A thin horizontal white rule at 20% opacity runs the full width of the screen, dividing the two panels at the exact vertical center. This rule pulses blue (`#0047FF`) for 0.3s then returns to white — emphasizing the architectural split.

**VO**: "The Telcoin Network runs a two-layer architecture. At the top: a consensus layer that orders every transaction. Below it: an execution layer that processes them. These two layers work together — but they're built for entirely different jobs."

**ON-SCREEN TEXT**:
- "CONSENSUS LAYER" (inside top panel)
- "Narwhal + Bullshark" (inside top panel)
- "EXECUTION LAYER" (inside bottom panel)
- "EVM-Compatible" (inside bottom panel)

**TRANSITION**: The two panels slide outward toward their respective screen edges — top panel rises off-screen top, bottom panel drops off-screen bottom. As they clear, the canvas is left with only the thin blue dividing line. That line then extends across the full canvas width and becomes the structural scaffold for Scene 3.

**VERTICAL CUT NOTE**: Stack both panels vertically in 9:16 with more vertical height per panel. The dividing line runs horizontally across mid-screen. Text legibility improves — increase font size 15% for vertical cut.

---

### SCENE 3 — THE CONSENSUS LAYER: NARWHAL + BULLSHARK DAG
**Duration**: 20 seconds
**Cumulative timecode**: 0:22 – 0:42

---

**VISUAL**:
The canvas fills with the deep navy background. The top half of the frame is designated as the consensus layer zone — indicated by a persistent thin `#0047FF` border strip along the top edge (4px tall, full width, 60% opacity).

A DAG (directed acyclic graph) node network builds in across the upper two-thirds of the canvas, animated from left to right:

**Node construction sequence** (timed to narration beats):
1. Six circular nodes appear left to right, in two rows of three — staggered vertically to create depth. Each node: 28px diameter, `#0047FF` fill, soft glow (bloom radius 20px, `#0047FF` at 40% opacity).
2. Directed edges draw in between nodes — animated as thin blue lines (1.5px, `#0047FF`) with a traveling dot (white, 6px) running along each edge to show directionality. Edge animation: 0.3s per line, with 0.1s stagger between edges.
3. A second "round" of three nodes appears to the right of the first cluster — same construction sequence. Edges link them back to nodes in the first round, demonstrating the parallel structure.
4. A third cluster of four nodes appears further right. By now the graph spans approximately 70% of the canvas width.

The nodes are labeled (small monospace text, 8px, `#8BA3C9`):
- First cluster labeled "Round 1"
- Second cluster labeled "Round 2"
- Third cluster labeled "Round 3"

A small "block" icon (rounded rectangle, 18px x 12px, white fill) slides out from the rightmost node in the third cluster, with a subtle motion trail. This represents the finalized block. It lands in a designated "FINALIZED" zone at the far right edge of the canvas — a small area delineated by a thin white vertical line.

**At 0:28s** (6 seconds into scene), a callout badge animates in below the DAG graph:
- Pill-shaped element, `#0047FF` background, white text
- Text: "Not a chain — a graph"
- Appears with a quick scale-up from 80% to 100% over 0.15s

**At 0:33s**, a split visual appears. The left quarter of the screen shows a traditional linear blockchain as a simple horizontal line of circles (white, 18px, connected by straight lines, labeled "Traditional chain" in `#8BA3C9`, 10px). This is deliberately simple — the point is contrast. A red X icon (`#FF4040`, 16px) appears above it at 0:35s.

The right three-quarters continues showing the live DAG animation, with the label "Telcoin: DAG consensus" appearing in white 13px text below the node graph. A green check icon (`#00C48C`, 16px) appears above the DAG at 0:35s.

**VO**: "The consensus layer uses Narwhal and Bullshark — a protocol adapted from Mysten Labs, the team behind the Sui blockchain. Instead of a linear chain of blocks, it builds a directed acyclic graph — a DAG. Multiple validators can propose and confirm transactions in parallel, simultaneously. This means consensus isn't a bottleneck — it's a parallel pipeline."

**ON-SCREEN TEXT**:
- "CONSENSUS LAYER" (persistent, top-left, small caps, `#8BA3C9`)
- "Narwhal + Bullshark DAG" (center, white, 18px, appears at 0:22)
- "Adapted from Mysten Labs / Sui" (`#8BA3C9`, 11px, appears at 0:24)
- "Round 1 / Round 2 / Round 3" (node cluster labels, monospace)
- "Not a chain — a graph" (pill badge, 0:28)
- "Traditional chain" (left panel label, 0:33)
- "Telcoin: DAG consensus" (right panel label, 0:33)

**TRANSITION**: The DAG graph contracts — all nodes shrink to 50% size and slide upward, compressing into a thin band at the top of the frame. This band persists into Scene 4 as a visual reminder that the consensus layer remains active while the execution layer takes focus.

**VERTICAL CUT NOTE**: For 9:16, run the DAG graph as a single vertical column — Round 1 at top, Round 2 in middle, Round 3 at bottom. Edges run top-to-bottom with directional dots flowing downward. The traditional chain vs. DAG comparison becomes a two-panel split: top half shows traditional chain, bottom half shows DAG. Remove the left/right split.

---

### SCENE 4 — THE EXECUTION LAYER: EVM + RUST
**Duration**: 16 seconds
**Cumulative timecode**: 0:42 – 0:58

---

**VISUAL**:
The compressed DAG band sits at the top of the canvas (`#0047FF` border, 6px) representing the consensus layer still running. The lower 85% of canvas is now the execution layer zone — fills with `#1A2744` as a background wash (full canvas fill, 30% opacity overlay — the deep navy still visible beneath).

A large Ethereum-diamond hexagon icon materializes in center-left of the canvas. Construction animation: the hexagon outline draws in clockwise over 0.4s in white (1.5px stroke). Once complete, the interior fills with `#1A2744`, and a soft white inner glow pulses once. The hexagon settles at 80px height.

Next to the hexagon, from right, three text elements fade in sequentially (0.2s stagger between each):
1. "EVM-Compatible" — white, 24px, medium weight
2. "Ethereum-standard smart contracts" — `#8BA3C9`, 14px
3. "Any developer already building on Ethereum can deploy here" — `#8BA3C9`, 12px, italic

**At 0:46s**, the Rust stat builds in below the hexagon text. Animation: a horizontal progress bar fills from left to right over 0.6s. The bar is gold (`#C9A227`), 6px tall, 260px wide. It fills to 99.4% of its width. Above the bar, a counter ticks from 0.0% to 99.4% over the same 0.6s — rendered in gold, 32px, medium weight. Below the bar, in `#8BA3C9` 11px:

```
of the codebase is written in Rust
```

**At 0:50s**, a small explanatory callout appears to the right of the Rust stat — rendered as a white card with `#0A0E1A` background, thin white border (1px, 20% opacity), 12px padding:

```
Rust = memory safety without a garbage collector.
Fewer attack surfaces. Higher throughput.
```

Text: `#8BA3C9`, 11px.

The card fades in with an opacity ease-in over 0.3s. No slide, no bounce.

**At 0:54s**, a short transaction lifecycle animation runs across the bottom of the frame — this is a horizontal data pipeline showing the handoff from consensus to execution:

```
[Ordered batch from DAG] → [EVM processes] → [State updated] → [Block finalized]
```

Each node is a rounded rectangle (50px x 24px), `#0D1526` fill, `#0047FF` border. Connecting arrows are animated (dotted blue lines, traveling dot). The entire pipeline draws in left to right over 1.5s.

**VO**: "Below the consensus layer sits the execution layer. It's EVM-compatible — meaning any developer already building on Ethereum can deploy directly on Telcoin Network without rewriting their contracts. The codebase is 99.4% Rust — a language chosen for memory safety, performance, and significantly fewer attack surfaces compared to alternatives."

**ON-SCREEN TEXT**:
- "EXECUTION LAYER" (top-left, persistent, small caps, `#8BA3C9`)
- "EVM-Compatible" (center, white, 24px)
- "99.4%" (gold, large stat, 0:46)
- "of the codebase is written in Rust" (`#8BA3C9`, below stat)
- "Ordered batch from DAG → EVM processes → State updated → Block finalized" (pipeline labels)
- "Chain ID: 2017  |  Gas token: TEL" (pill badges, bottom-right, appear at 0:56s)

**TRANSITION**: The EVM hexagon and Rust stat slide to the left edge of the canvas and compress into a small badge cluster — they become a permanent left-rail element that persists into Scene 5. The right two-thirds of canvas opens up for the validator segment.

**VERTICAL CUT NOTE**: Stack the EVM hexagon and Rust stat vertically. Hexagon at top with text below it, Rust progress bar below that. Drop the horizontal pipeline — replace with a vertical flow arrow (top to bottom) with the same four labels. Chain ID / TEL badges move to bottom of frame.

---

### SCENE 5 — THE VALIDATORS: GSMA MNOs
**Duration**: 22 seconds
**Cumulative timecode**: 0:58 – 1:20

---

**VISUAL**:
This is the most complex scene. Open on a mostly clear canvas with the architecture badge cluster at the left rail (small, from Scene 4's transition).

**Phase A — Who validates (0:58 – 1:06, 8 seconds)**:

Five validator node tiles materialize vertically in the right-center of the canvas, staggered in with a 0.1s delay between each. Each tile is:
- 160px wide x 56px tall
- `#0D1526` background
- White border, 1px, 30% opacity
- Left side: small signal tower icon (two horizontal bars + arc above, white, 20px) — the universal cellular broadcast glyph
- Right side: text label "MNO Validator" in `#8BA3C9`, 11px

The tiles sit in a vertical stack with 8px gap between each.

At 1:00s (2 seconds in), the second tile from the top pulses — its border transitions to `#0047FF` (solid, 1.5px), its background brightens slightly (opacity increase from 0% to 8% `#0047FF` fill). A small dot ("block produced" indicator) appears at the tile's right edge and travels rightward to a "BLOCK" landing zone icon (white rounded square, 30px, positioned 40px to the right of the tile stack).

**Phase B — The GSMA badge appears (1:06 – 1:10, 4 seconds)**:

Below the validator tile stack, a pill-shaped badge scales up from 0 to 100% over 0.25s with an ease-out spring:
- `#0047FF` background
- White text: "GSMA Full-Member MNOs Only"
- 14px, medium weight
- 12px vertical padding, 24px horizontal padding
- Soft drop shadow: `#0047FF` at 40% opacity, 0px offset, 12px blur

Below the badge, two lines of text fade in at 0.2s stagger:
- "Must stake TEL to participate" (white, 11px)
- "Only licensed telecom operators earn network fees" (`#8BA3C9`, 11px)

**Phase C — The distribution reveal (1:10 – 1:20, 10 seconds)**:

This is the scene's emotional peak — the moment where the viewer realizes the validator model doubles as a distribution network.

At 1:10s, each validator tile expands horizontally to the left — its width extends from 160px to 280px. The new left section that appears is a darker panel (`#060912`) containing a number:

- Tile 1 expansion: "40M+ subscribers" (white, 13px)
- Tile 2 expansion: "80M+ subscribers" (white, 13px)
- Tile 3 expansion: "120M+ subscribers" (white, 13px)
- Tile 4 expansion: "55M+ subscribers" (white, 13px)
- Tile 5 expansion: "90M+ subscribers" (white, 13px)

**Note to motion designer**: These subscriber numbers are illustrative — they represent the scale of typical GSMA member MNO subscriber bases, not specific named MNO figures. Do not caption these with specific MNO names. A footnote lower-third reads: "Subscriber counts illustrative — represent scale of typical GSMA MNO operators."

The expansion animation runs tile by tile with a 0.12s stagger, each tile sliding its left edge outward over 0.3s.

After all tiles have expanded, a callout text block materializes to the left of the expanded tiles (white, 15px, with `#0047FF` left-border accent, 3px):

```
Every MNO that validates
is also a live distribution channel
to its subscriber base.
```

This text appears word by word in a 0.8s reveal, left to right.

A subtle arc bracket (curved brace icon, `#0047FF`, 2px stroke) spans all five subscriber counts and terminates at a label: "Millions of potential users per validator" (`#8BA3C9`, 10px, italic).

**VO**: "Who validates the network? Only GSMA full-member mobile network operators — licensed telecoms that must stake TEL to participate. This isn't just a validator requirement — it's an architectural choice. Every MNO that joins the validator set is also a direct distribution channel to its subscriber base. The validator and the distribution network are the same entity."

**ON-SCREEN TEXT**:
- "VALIDATORS" (top, all-caps, `#8BA3C9`, small caps)
- "MNO Validator" (on each tile)
- "GSMA Full-Member MNOs Only" (badge)
- "Must stake TEL to participate" (below badge)
- "Only licensed telecom operators earn network fees" (below badge)
- "[N]M+ subscribers" (on each expanded tile — illustrative)
- "Every MNO that validates / is also a live distribution channel / to its subscriber base." (callout)
- "Subscriber counts illustrative — represent scale of typical GSMA MNO operators." (footnote, 8px, `#8BA3C9`)

**TRANSITION**: The validator tiles shrink back to their minimal form and arrange themselves in a circular arc — 5 nodes curving across the top of the canvas. Below them, the flywheel animation begins building in (Scene 6). The transition takes 0.4s.

**VERTICAL CUT NOTE**: In 9:16, the validator tiles run horizontally across the frame (rotated 90 degrees conceptually — each tile is a horizontal strip running full width). The subscriber count expansion happens downward (tile extends vertically down). The distribution callout text moves to below the tile stack. This is the most significant layout change across all scenes.

---

### SCENE 6 — THE FLYWHEEL
**Duration**: 16 seconds
**Cumulative timecode**: 1:20 – 1:36

---

**VISUAL**:
The five validator arc from Scene 5's transition sits at the top of the canvas — five small `#0047FF` nodes in a curved line, each labeled "MNO" in `#8BA3C9`, 9px.

In the center of the canvas, the flywheel builds in three stages:

**Stage 1 — The circular path draws (1:20 – 1:23, 3 seconds)**:
A circular track draws in — a ring of dashes (`#0047FF`, 60% opacity, 2px) forming a full circle at 200px diameter. The ring draws clockwise over 0.8s. Three nodes appear at 12 o'clock, 4 o'clock, and 8 o'clock positions — each is a 36px diameter circle, `#0D1526` fill with `#0047FF` border (1.5px).

**Stage 2 — Labels appear (1:23 – 1:26, 3 seconds)**:
Text fades into each node (0.1s stagger):
- 12 o'clock node: "Usage" (white, 13px, center-aligned)
- 4 o'clock node: "Fees" (white, 13px, center-aligned)
- 8 o'clock node: "MNO Promotion" (white, 11px, center-aligned — slightly smaller to fit)

Curved arrows appear along the circular track between each node, animated as a traveling highlight. The highlight is a white dot (8px) that travels along the dashed ring from Usage → Fees → MNO Promotion → back to Usage, in a continuous loop starting at 1:26. Loop cycle duration: 2.4 seconds.

**Stage 3 — The explanation populates (1:26 – 1:36, 10 seconds)**:
As the flywheel spins, annotation text appears adjacent to each node in sequence, timed to VO beats:

- **Usage node** (at 1:26): A small annotation line extends right from the node. Text: "Telcoin services used on MNO networks" (`#8BA3C9`, 10px)
- **Fees node** (at 1:29): A small annotation line extends right. Text: "MNO earns transaction fees from network" (`#8BA3C9`, 10px)
- **MNO Promotion node** (at 1:32): A small annotation line extends left. Text: "MNO promotes Telcoin to grow revenue" (`#8BA3C9`, 10px)

At 1:33s, the flywheel ring gets a single full-brightness highlight pass — the entire ring flashes `#0047FF` at 100% opacity then dims back to 60% over 0.4s. A small "+" icon appears at the Usage node: "More users → More usage" (white, 11px).

The five MNO arc nodes at the top of the canvas send thin dotted lines downward to the flywheel ring — connecting the validator set to the flywheel, showing the mechanism is the same system.

**VO**: "The economics close into a flywheel. When Telcoin services are used on an MNO's network, that MNO earns transaction fees. Those fees create a direct incentive for the MNO to promote Telcoin services to its subscribers — which drives more usage, which generates more fees. Each new MNO validator doesn't just extend the network's security — it extends its reach."

**ON-SCREEN TEXT**:
- "THE FLYWHEEL" (top-center, small caps, `#8BA3C9`, appears at 1:20)
- "Usage" (flywheel node)
- "Fees" (flywheel node)
- "MNO Promotion" (flywheel node)
- "Telcoin services used on MNO networks" (annotation)
- "MNO earns transaction fees from network" (annotation)
- "MNO promotes Telcoin to grow revenue" (annotation)
- "More users → More usage" (callout, 1:33)

**TRANSITION**: The flywheel scales down to 30% size and slides to bottom-left corner of the canvas, where it continues spinning (loop animation, very small). The canvas opens to show the final scene — a clean summary layout.

**VERTICAL CUT NOTE**: In 9:16, the flywheel is centered horizontally, and the annotations appear below each node (since there's room below in the vertical format). The MNO arc runs across the top of the 9:16 frame. The flywheel is scaled up slightly to 240px diameter to fill the vertical canvas better.

---

### SCENE 7 — NETWORK STATUS + CTA
**Duration**: 12 seconds
**Cumulative timecode**: 1:36 – 1:48

---

**VISUAL**:
Clean dark canvas. The flywheel persists as a small looping element in the bottom-left (30px — subtle, not distracting).

The scene opens with the architecture summary building in — this is the "how it all fits" beat.

**Left third of canvas** — a compressed version of the two-layer architecture (from Scene 2) fades in. Both panels are at 50% of their original size, stacked. No animation — they appear as settled elements, labels visible:
- Top: "Narwhal + Bullshark" (white, 13px)
- Bottom: "EVM-Compatible" (white, 13px)

**Center of canvas** — network status block:
A card element (`#0D1526` background, `#0047FF` border 1px, 16px padding) appears:
- Top label: "NETWORK STATUS" (all-caps, `#8BA3C9`, 10px, letter-spacing 0.12em)
- Status indicator: a green dot (8px, `#00C48C`, soft glow) followed by "Adiri Testnet — Active" (white, 16px, medium weight)
- Below: "Mainnet: pending final security audits and MNO onboarding" (`#8BA3C9`, 12px)
- Below that: a small roadmap link in `#0047FF`, 11px: "roadmap.telcoin.network"

The status card fades in over 0.3s.

**At 1:40s**, the CTA block builds in:
The Telcoin wordmark (white, ~32px height) fades in above the center status card. Below the status card, the primary URL materializes:

```
telcoin.network
```

White, 22px, medium weight. Below that, the X handle:

```
@telcoinTAO
```

`#0047FF`, 16px.

**At 1:43s**, a thin horizontal rule (`#0047FF`, 1px, 20% opacity) runs full-width across the canvas. Below it, three mini-stat columns appear in sequence (0.15s stagger):

| Column 1 | Column 2 | Column 3 |
|---|---|---|
| "L1" (white, 20px) | "Rust 99.4%" (gold, 20px) | "GSMA MNOs" (white, 20px) |
| "EVM-Compatible Layer 1" (`#8BA3C9`, 10px) | "Codebase language" (`#8BA3C9`, 10px) | "Exclusive validator class" (`#8BA3C9`, 10px) |

Each stat column is separated by a thin vertical `#0047FF` rule (1px, 40% opacity).

The full frame holds for 2.5 seconds.

**At 1:46s**, a subtle grid of faint blue dots fades in as a background texture — the same node graph from Scene 1's opening, but very faint (3% opacity), completing the visual bookend.

**Fade to black**: Begins at 1:47s, completes at 1:48s. The Telcoin wordmark lingers for an extra 0.5s after everything else goes black — white on black — then fades. Total black hold: 0.5s.

**VO**: "The Adiri testnet is live. Mainnet launch follows the completion of final security audits and MNO validator onboarding — milestone-based, not calendar-based. For full roadmap status, visit telcoin.network."

**ON-SCREEN TEXT**:
- "NETWORK STATUS"
- "Adiri Testnet — Active" (with green status dot)
- "Mainnet: pending final security audits and MNO onboarding"
- "roadmap.telcoin.network"
- Telcoin wordmark
- "telcoin.network"
- "@telcoinTAO"
- Mini-stats: "L1 / EVM-Compatible Layer 1", "Rust 99.4% / Codebase language", "GSMA MNOs / Exclusive validator class"

**TRANSITION**: Fade to black. End card.

**VERTICAL CUT NOTE**: In 9:16, drop the left-third architecture summary (no room). The status card fills center-frame. Stats run as a 3-row vertical list rather than 3-column horizontal row. URL and handle at bottom of frame, Telcoin wordmark at top of frame.

---

## FULL SCRIPT — VOICEOVER ONLY

*(Clean read for recording session — all narration, no stage directions)*

---

"Most blockchains solve one problem. Telcoin Network was built to solve two.

The Telcoin Network runs a two-layer architecture. At the top: a consensus layer that orders every transaction. Below it: an execution layer that processes them. These two layers work together — but they're built for entirely different jobs.

The consensus layer uses Narwhal and Bullshark — a protocol adapted from Mysten Labs, the team behind the Sui blockchain. Instead of a linear chain of blocks, it builds a directed acyclic graph — a DAG. Multiple validators can propose and confirm transactions in parallel, simultaneously. This means consensus isn't a bottleneck — it's a parallel pipeline.

Below the consensus layer sits the execution layer. It's EVM-compatible — meaning any developer already building on Ethereum can deploy directly on Telcoin Network without rewriting their contracts. The codebase is 99.4% Rust — a language chosen for memory safety, performance, and significantly fewer attack surfaces compared to alternatives.

Who validates the network? Only GSMA full-member mobile network operators — licensed telecoms that must stake TEL to participate. This isn't just a validator requirement — it's an architectural choice. Every MNO that joins the validator set is also a direct distribution channel to its subscriber base. The validator and the distribution network are the same entity.

The economics close into a flywheel. When Telcoin services are used on an MNO's network, that MNO earns transaction fees. Those fees create a direct incentive for the MNO to promote Telcoin services to its subscribers — which drives more usage, which generates more fees. Each new MNO validator doesn't just extend the network's security — it extends its reach.

The Adiri testnet is live. Mainnet launch follows the completion of final security audits and MNO validator onboarding — milestone-based, not calendar-based. For full roadmap status, visit telcoin.network."

---

**Total word count**: ~310 words
**Estimated read time at 175 WPM (calm, authoritative pace)**: ~106 seconds
**Target**: 105 seconds — on spec

---

## PRODUCTION NOTES

---

### 1. RECOMMENDED MOTION GRAPHICS TOOLCHAIN

**Primary recommendation — After Effects (Adobe CC)**

- **Animation**: After Effects CC with the following plugin stack:
  - **Motion Bro** (preset manager) — organize and apply graph animation presets
  - **Flow** (by aescripts) — custom easing curves; use for all node/panel entrance animations (avoid AE's default Easy Ease — too soft for this technical aesthetic)
  - **Overlord** (by Battleaxe) — Illustrator-to-AE vector transfer; use for DAG node graphs and all icon elements built in Illustrator
  - **Rubberhose 2** or **RubberPin** — not needed here (no character animation), but useful for future explainer work
  - **DUIK Bassel** — not needed for this video; relevant if adding any rigged character elements later
  - **Optical Flares** (Video Copilot) — for the `#0047FF` node bloom/glow effects in Scene 1 and Scene 3
  - **Element 3D** — not needed; keep this video strictly 2D flat

- **Vector prep**: Adobe Illustrator CC — build all icons (DAG nodes, EVM hexagon, signal tower, flywheel arc) as vectors, import via Overlord

- **Typography rendering**: Render all text elements natively in AE using installed Inter or Neue Haas Grotesk. Do not composite text via Illustrator — AE's text engine handles the fade-in and per-character animations required in Scene 1.

**Alternative recommendation — Rive (for web-native deployment)**

If the video is intended for interactive web embedding (e.g., on telcoin.network homepage or a dedicated network explainer page), Rive is the preferred tool:
- All animations are vector-based, state-machine driven, and load at <200KB
- Rive animations can respond to scroll position — ideal for an interactive architecture page where each section of the animation triggers as the user scrolls
- The DAG node graph (Scene 3) and flywheel (Scene 6) are well-suited to Rive's node-based animation system
- Export: Rive runtime embeds directly in React/Next.js — no video file needed
- Limitation: The motion blur and bloom glow effects require post-processing in AE if a video export is also needed; Rive renders are crisp but lack raster effects

**Third option — Jitter (faster production, reduced fidelity)**
Jitter is appropriate if turnaround time is under 48 hours and fidelity requirements are relaxed. It will handle all basic panel animations and text reveals. It cannot reproduce the DAG graph's directional traveling-dot animations or the Optical Flares bloom — those would need to be pre-rendered and composited in.

---

### 2. MUSIC DIRECTION

**Mood**: Technical precision meets forward motion. Not ambient drone. Not EDM. Not corporate elevator. The reference frame is the score to a well-made infrastructure documentary — think: the quieter tracks from Hans Zimmer's "Interstellar" score minus the organ, or the minimal electronic compositions Nils Frahm writes for film work. Purposeful, tonal, slightly cold in a compelling way.

**Tempo**: 80–92 BPM. Slow enough to feel considered, fast enough to hold attention. No tempo changes mid-video — consistency signals technical confidence.

**Instrumentation**: Synthesizer pads (held chords), subtle bass pulse (not a beat — a low-end harmonic), sparse piano or marimba top notes for texture. No drums. No guitar. No vocals.

**Dynamics**: Starts quiet (Scene 1 — nearly silent). Grows slowly through Scenes 2–3. Peaks in energy at Scene 5 (validator reveal) — not louder, but denser harmonically. Resolves back to single pad tone for Scene 7 CTA.

**Music library references (for licensing)**:
- **Musicbed**: Search "technical, minimal, cinematic electronic" — filter to "corporate" category but exclude "upbeat" tags
- **Artlist**: "Atmospheric, slow, electronic" — look for tracks by Liqvid or similar
- **Epidemic Sound**: "Documentary, science, space" category — avoid anything with build-drop structure

**Volume treatment**: Music sits at -20 dB under VO. VO is king. Music should be inaudible without headphones and present but not distracting with headphones.

---

### 3. VOICEOVER CASTING DIRECTION

**Target demographic for narrator**: Male or female — no preference, but voice must read as technically credible, not as a "brand voice." Avoid voices that sound like they belong in a car commercial or a wellness app.

**Vocal qualities to cast for**:
- Pace: 160–180 WPM. Never rushes. Pauses at the end of clauses, not just at full stops.
- Register: Mid-low. Chest voice, not head voice. The kind of voice that sounds like it knows what it's talking about without needing to tell you it does.
- Accent: Neutral American, neutral British, or neutral mid-Atlantic. Avoid strong regional accents (Southern US, Texan, Boston, Liverpool, Australian) — not because they're bad but because they carry narrative implications that distract from technical content.
- References: The narrator of any BBC Four science documentary; the English voiceover track on a well-produced Kurzgesagt video; Lex Fridman's interview pacing (without the specific vocal timbre).

**Delivery notes for the session**:
- The phrase "directed acyclic graph — a DAG" (Scene 3): emphasize "a DAG" as a definition moment — slight downward inflection, not upward (this is a statement, not a question)
- "The validator and the distribution network are the same entity." (Scene 5): full stop after "entity" — this is the thesis sentence. Give it room. Do not rush into the next line.
- "Milestone-based, not calendar-based." (Scene 7): read the em-dash clause as a clarification addendum, slightly quieter, faster than the preceding phrase
- No "radio voice" performance — conversational within professional bounds; the listener should feel addressed, not broadcast-at

**Recording spec**: 48kHz / 24-bit WAV. Record in a treated room or professional booth. No noise reduction artifacts — they degrade quality more than a small amount of room tone.

---

### 4. RUNWAY ML / KLING PROMPTS — AMBIENT BACKGROUND ANIMATIONS

These three prompts are for scene-level generative background texture generation only. They are not the primary animation — they serve as subtle animated backgrounds composited at 8–12% opacity beneath the motion graphics layer.

---

**Prompt 1 — Scene 1 and Scene 2 (DAG particle field background)**

For Runway Gen-3 Alpha / Kling v1.5:

```
Abstract network of glowing blue particles on a near-black background. Particles
are small (2–4px equivalent), connected by thin luminous lines forming a sparse
graph structure. Particle movement is slow and organic — each node drifts 5–15px
over 8 seconds in a gentle random walk, then reverses. Lines connecting adjacent
particles pulse with traveling light dots moving along them. Color palette: deep
navy-black background (#0A0E1A equivalent), bright electric blue (#0047FF) for
particles and lines. No camera movement. Static frame with internal motion only.
Cinematic, 24fps. Dark, technical, cold aesthetic. No lens flare. No chromatic
aberration. Loopable 8-second clip.
```

*Composite at 8% opacity beneath Scene 1 and Scene 2 motion graphics. Used as environmental atmosphere, not foreground element.*

---

**Prompt 2 — Scene 3 (DAG graph depth field — behind the primary DAG animation)**

For Runway Gen-3 Alpha / Kling v1.5:

```
Distant, out-of-focus network graph visualization. Dozens of small nodes and
edges visible in soft bokeh — like looking through glass at a data center
visualization. Color: deep blue-navy tones, electric blue highlights at 20%
opacity. Nodes slowly blink in and out — random intervals, 2–4 second cycles.
Very slight horizontal drift — entire field moves left at 4px per second as
if on a slow dolly. No sharp focus anywhere in frame. No text. No recognizable
symbols. Abstract data infrastructure atmosphere. Dark, cold, technical. Loopable
10-second clip.
```

*Composite at 10% opacity behind the DAG node animation in Scene 3. The in-focus DAG nodes sit on top — this creates a sense of depth, implying a larger network behind what's being shown.*

---

**Prompt 3 — Scene 7 (deep space / infrastructure ambient — CTA closing shot)**

For Runway Gen-3 Alpha / Kling v1.5:

```
Extreme slow zoom out from a dense field of blue-white data points arranged in
a loose spherical cluster — like a star field but structured, suggesting network
topology. Background is absolute black. Points are tiny (1–2px equivalent), each
with a slight directional glow trail showing very slow movement outward from
center. The overall impression is: infrastructure at planetary scale. Cold, clean,
awe-inducing but not dramatic. No color variation — strict blue-white and black.
No camera shake. No lens effects. Loopable 12-second clip. 24fps.
```

*Composite at 6% opacity in Scene 7 behind the CTA card layout. This is the most subtle of the three — barely perceptible, but adds dimensionality to what would otherwise be a flat dark canvas.*

---

### 5. SCENE RUNTIME AND CUMULATIVE TIMECODES

| Scene | Title | Duration | In Point | Out Point |
|---|---|---|---|---|
| 1 | Hook | 8s | 0:00 | 0:08 |
| 2 | Two-Layer Architecture | 14s | 0:08 | 0:22 |
| 3 | Consensus Layer — DAG | 20s | 0:22 | 0:42 |
| 4 | Execution Layer — EVM + Rust | 16s | 0:42 | 0:58 |
| 5 | The Validators — GSMA MNOs | 22s | 0:58 | 1:20 |
| 6 | The Flywheel | 16s | 1:20 | 1:36 |
| 7 | Network Status + CTA | 12s | 1:36 | 1:48 |
| — | **Total** | **108s** | — | — |

*Target: 105s. Narration runs 106s at 175 WPM. Buffer: edit Scene 1's silence down by 1 second (reduce the pre-VO hold from 3.5s to 2.5s) and tighten Scene 7's closing hold by 1 second. Achieves 105s final cut.*

---

### 6. ADDITIONAL PRODUCTION GUIDANCE

**Aspect ratio deliverables**:
- Primary: 1920x1080px, 16:9, 24fps (YouTube / Twitter)
- Secondary: 1080x1920px, 9:16, 24fps (TikTok / Reels) — using 9:16 cut notes per scene above
- Optional: 1080x1080px, 1:1, 24fps (Instagram feed) — use Scene 5 and Scene 6 only, cut to 30s social short

**File delivery format**: H.264 or H.265 MP4, 4K source file for remastering. Deliver project file (AEP or Rive source) alongside renders.

**Export settings**:
- Codec: H.264 (for social delivery), ProRes 4444 (for master archive)
- Color space: sRGB for web delivery; Rec. 709 for broadcast-safe check
- Audio: AAC 320kbps stereo mixed; deliver separate stems (VO stem, music stem, mixed master)

**Accessibility**:
- Closed captions: Yes — deliver SRT file timed to VO
- Caption burn-in option: Required for TikTok / Reels version (auto-captions are not reliable for technical terminology like "Narwhal," "Bullshark," "DAG," "EVM," "QUIC-v1")
- Color contrast: All on-screen text must meet WCAG 2.1 AA — white on `#0A0E1A` passes at all tested sizes; `#8BA3C9` on `#0A0E1A` passes at 12px+ (verify with Figma contrast plugin before export)
- Motion sensitivity: All particle field backgrounds should be composited at low opacity and slow velocity — not compliant for WCAG 2.3.3 (Animation from Interactions) but within acceptable range for ambient background motion at <3px/second apparent movement

**Approval gate**: Share Scene 3 (DAG animation) and Scene 5 (Validator reveal) as animatic previews before full production. These are the two highest-complexity scenes and the most likely points of revision. Locking them early saves production time on the full render pass.

---

*Script authored: March 12, 2026*
*Source brief: `/home/user/Telcoin-Association-Agency/design/output/network-infographic-brief.md`*
*Research source: `/home/user/Telcoin-Association-Agency/campaign/research/TELCOIN-RESEARCH.md`*
*Output file: `/home/user/Telcoin-Association-Agency/design/output/network-explainer-video-script.md`*
*Authored by: Visual Storyteller — Telcoin Association Marketing Agency*
