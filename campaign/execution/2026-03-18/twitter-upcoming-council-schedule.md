# Twitter Post: Upcoming Council Meeting Schedule
**Account**: @telcoinTAO
**Date**: March 18, 2026
**Tier**: 1 - Governance
**Format**: Single tweet
**File**: `campaign/execution/2026-03-18/twitter-upcoming-council-schedule.md`

---

## Tweet Copy

Telcoin Association council meetings - upcoming schedule:

Mar 18 - TELx Council - 3:00 PM EST / 19:00 UTC
Mar 26 - P&T Council - 4:00 PM EST / 20:00 UTC
Apr 1 - TELx Council - 3:00 PM EST / 19:00 UTC
Apr 2 - TAN Council - 5:00 PM EST / 21:00 UTC

Community members may observe via Telcoin Association Discord.

Agenda and minutes: forum.telcoin.org

---

**Character count**: ~265 (under 280 limit)

**Checklist:**
- No emojis
- No contractions
- No enthusiasm language
- No conversation prompt (Tier 1 governance)
- No em dashes (hyphens used throughout)
- Both EST and UTC times included
- Forum link included
- Discord observation noted
- Institutional tone throughout
- Link placed at end, not at open

---

## Tweet Card Design Brief

**Asset type**: Static image - Tweet card
**Dimensions**: 1200 x 675 px
**Placement**: Attached to tweet above

---

### Purpose

Institutional schedule card for Telcoin Association council meetings. Reads as a structured calendar announcement - not a promotional graphic. The design should resemble a formal meeting notice or regulatory publication schedule, not a marketing banner.

---

### Layout - Figma Spec

**Canvas**
- Width: 1200 px
- Height: 675 px
- Background: TEL Black #090920
- Corner radius: 0 px (full bleed, no card rounding - institutional, not branded card style)

---

**Zone 1 - Header (top stripe)**
- Height: 80 px
- Background: TEL Royal Blue #3642B2
- Content, left-aligned with 48 px left padding:
  - Logo: Telcoin Association horizontal lockup (hexagon mark + wordmark) - white version
  - Logo height: 32 px
  - Vertical center within stripe
- Content, right-aligned with 48 px right padding:
  - Label text: "COUNCIL SCHEDULE"
  - Font: New Hero Bold (Inter Bold fallback)
  - Size: 11 px
  - Letter spacing: 0.15 em (all caps tracking)
  - Color: TEL White #F1F4FF
  - Opacity: 70%
  - Vertical center within stripe

---

**Zone 2 - Title block (below header)**
- Top padding from header: 40 px
- Left padding: 64 px
- Content:
  - Line 1: "Telcoin Association"
    - Font: New Hero Regular (Inter Regular fallback)
    - Size: 14 px
    - Color: TEL Blue #14C8FF
    - Letter spacing: 0.08 em
    - Text transform: uppercase
  - Line 2: "Council Meetings"
    - Font: New Hero Bold (Inter Bold fallback)
    - Size: 32 px
    - Color: TEL White #F1F4FF
    - Margin top: 6 px
  - Line 3: "March - April 2026"
    - Font: New Hero Regular (Inter Regular fallback)
    - Size: 16 px
    - Color: TEL White #F1F4FF
    - Opacity: 55%
    - Margin top: 8 px

---

**Zone 3 - Schedule table (center body)**
- Top margin from title block: 36 px
- Left padding: 64 px
- Right padding: 64 px
- Table width: full canvas width minus left and right padding (1072 px usable)

**Table structure:**
- 4 rows, one per meeting
- No outer border
- Row separator: 1 px horizontal line, color TEL Royal Blue #3642B2, opacity 30%
- Row height: 68 px
- Vertical alignment: center

**Column layout (left to right):**

| Column | Label | Width | Content |
|---|---|---|---|
| A - Date | No header | 140 px | Date string |
| B - Council | No header | 260 px | Council name |
| C - Time EST | No header | 240 px | EST time |
| D - Time UTC | No header | 240 px | UTC time |
| E - Status | No header | 192 px | Status badge (most recent only) |

**Column A - Date**
- Font: New Hero Bold (Inter Bold fallback)
- Size: 15 px
- Color: TEL White #F1F4FF

**Column B - Council name**
- Font: New Hero Regular (Inter Regular fallback)
- Size: 15 px
- Color: TEL White #F1F4FF
- Opacity: 85%

**Column C - EST time**
- Font: New Hero Regular (Inter Regular fallback)
- Size: 14 px
- Color: TEL White #F1F4FF
- Opacity: 65%
- Prefix label "EST" in TEL Blue #14C8FF, size 10 px, letter spacing 0.1 em, rendered left of time string with 4 px gap

**Column D - UTC time**
- Same treatment as Column C
- Prefix label "UTC" in TEL Blue #14C8FF

**Column E - Status badge (Row 1 only - Mar 18)**
- Pill badge: "Most Recent" or leave blank and use a thin left-border accent instead
- Preferred treatment: 2 px left border accent on the row in TEL Blue #14C8FF, no badge text - cleaner, more institutional
- Rows 2-4: no badge

**Row data:**

| Row | Date | Council | EST | UTC |
|---|---|---|---|---|
| 1 | Mar 18 | TELx Council | 3:00 PM | 19:00 |
| 2 | Mar 26 | P&T Council | 4:00 PM | 20:00 |
| 3 | Apr 1 | TELx Council | 3:00 PM | 19:00 |
| 4 | Apr 2 | TAN Council | 5:00 PM | 21:00 |

---

**Zone 4 - Footer (bottom of canvas)**
- Height: 56 px
- Background: solid #0D0F1F (slightly lighter than TEL Black - creates subtle separation without a border)
- Left-aligned content, 64 px left padding, vertically centered:
  - "Observe via Telcoin Association Discord"
  - Font: New Hero Regular (Inter Regular fallback)
  - Size: 11 px
  - Color: TEL White #F1F4FF
  - Opacity: 45%
- Right-aligned content, 64 px right padding, vertically centered:
  - "forum.telcoin.org"
  - Font: New Hero Regular (Inter Regular fallback)
  - Size: 11 px
  - Color: TEL Blue #14C8FF
  - Opacity: 80%

---

### Visual Accent

- Optional: subtle geometric hexagon motif in lower-right quadrant of Zone 3 background
  - Single large hexagon outline (no fill), opacity 3-5%, color TEL Royal Blue #3642B2
  - Scale: approximately 320 px wide
  - Do not let it overlap any table text
  - Purpose: brand texture only - must not read as decorative or draw the eye

---

### Typography Summary

| Element | Typeface | Weight | Size | Color |
|---|---|---|---|---|
| Header label | New Hero / Inter | Bold | 11 px | #F1F4FF at 70% |
| Subtitle line 1 | New Hero / Inter | Regular | 14 px | #14C8FF |
| Title | New Hero / Inter | Bold | 32 px | #F1F4FF |
| Date range | New Hero / Inter | Regular | 16 px | #F1F4FF at 55% |
| Table - date | New Hero / Inter | Bold | 15 px | #F1F4FF |
| Table - council | New Hero / Inter | Regular | 15 px | #F1F4FF at 85% |
| Table - time labels | New Hero / Inter | Regular | 10 px | #14C8FF |
| Table - time values | New Hero / Inter | Regular | 14 px | #F1F4FF at 65% |
| Footer text | New Hero / Inter | Regular | 11 px | #F1F4FF at 45% |
| Footer URL | New Hero / Inter | Regular | 11 px | #14C8FF at 80% |

---

### Color Palette Reference

| Token | Hex | Usage |
|---|---|---|
| TEL Black | #090920 | Canvas background |
| TEL Royal Blue | #3642B2 | Header stripe, row dividers, hexagon accent |
| TEL Blue | #14C8FF | Accent labels, time prefix labels, URL, left-border accent |
| TEL White | #F1F4FF | All body text |
| Footer background | #0D0F1F | Footer zone |

---

### Production Notes

- No text inside AI-generated imagery - this card is Figma-native, no AI image required
- All text is placed directly in Figma
- Export at 2x (2400 x 1350 px) for retina - compress to under 1 MB for Twitter upload
- Do not add drop shadows, gradients, or glow effects on text - flat typography only
- The hexagon accent (if used) should be a vector shape, not a raster image
- Logo: use the approved horizontal lockup asset from the Figma brand library (white version on dark)

---

## Publishing Notes

- Post date: March 18, 2026 or as soon as image is produced
- No scheduling delay required - informational, time-sensitive
- No launch window required for Tier 1 governance posts
- Do not boost or promote as paid post

