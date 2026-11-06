---
description: Generate a YouTube thumbnail for a project with Ideogram 4
---

# Thumbnail

Generate a 1280×720 thumbnail for a project: a short hook phrase in big legible text, in
the brand's colours, ready for `/publish --thumbnail`. Wraps `tools/ideogram4.py`.

```
project.json + script + brand.json → hook phrase → JSON caption → Ideogram 4 → check text → out/thumbnail.png
```

Claude does the creative part: it picks the phrase and writes the caption. Ideogram renders
text reliably **only from a structured JSON caption**. A plain `--prompt` adds garbled
filler text. Load the `ideogram4` skill (`SKILL.md`, `prompting.md`, `examples.md` §2)
before writing the caption.

> **Needs `IDEOGRAM_API_KEY` in `.env`** (key from developer.ideogram.ai). If it's missing,
> say so and stop. Cost: ~$0.10 per image at `--speed QUALITY`. Tell the user the total
> before generating more than one.

## Entry Point

### Step 1: Locate the project

If the user named a project, use it. Otherwise list candidates and ask:

```bash
cd /path/to/claude-code-video-toolkit && ls projects/*/project.json
```

If `out/thumbnail.*` already exists, show it and ask whether to replace it or keep it.

### Step 2: Gather what the video is about

`project.json` is often sparse (null titles and narration), so read the content from wherever it is:

1. `project.json`: `publish.title`, `title`, `name`, `description`, `brand`, and each
   scene's `title` and `narration`
2. `VOICEOVER-SCRIPT.md`, which usually has the clearest statement of the topic
3. The template config (`src/config/*.ts`, e.g. `sprint-config.ts` or `demo-config.ts`),
   for the title slide text and any stats
4. `scenes.json` for concept-explainer-short projects

Then read `brands/<brand>/brand.json`. Pick **3–4 colours**: a dark or light background,
the primary or accent colour, and a high-contrast text colour (usually white). Don't pass
`--brand` to the tool. It injects every colour in brand.json, including dividers, shadows
and greys, which muddies the palette.

### Step 3: Choose the hook phrase

The thumbnail text is **not** the video title. Thumbnails are read in under a second,
next to the title, which YouTube shows anyway.

- **1–3 words** for the main phrase. Ideogram renders text best at that length, and it
  stays readable at phone size. An optional 1–3 word subhead is fine.
- Concrete beats clever: the feature, the outcome, the number ("SCREEN SHARE",
  "2× FASTER", "v2 IS HERE").
- Avoid repeating the title word for word.

Propose **2–3 options** and a one-line visual idea for each (what sits beside the text).
Let the user pick or edit. Accept a phrase the user gives directly.

### Step 4: Write the caption

Write the caption to `projects/NAME/thumbnail/caption.json` so it can be reviewed and re-run.
Start from `examples.md` §2 (thumbnail) and keep these layout rules:

| Rule | Why |
|------|-----|
| Text as a `text` element with the exact string, in a `bbox` on the left ~half (e.g. `[180,50,620,540]`) | Bboxes are `[y_min,x_min,y_max,x_max]`, 0–1000. Left-side text is the convention viewers scan for |
| Keep everything important out of the **bottom-right corner** (`y>800, x>780`) | YouTube overlays the duration badge there |
| One visual subject on the other side, as an `obj` element | A single clear subject reads at small sizes. Busy scenes don't |
| `desc` the text as "massive heavy sans-serif, all caps, crisp white" (or the brand's text colour) | High contrast against the background is what makes it legible in a feed |
| Don't ask for a logo | Ideogram can't reproduce a real logo. It invents a lookalike |

### Step 5: Generate

```bash
cd /path/to/claude-code-video-toolkit && mkdir -p projects/NAME/out && \
  uv run tools/ideogram4.py --json projects/NAME/thumbnail/caption.json \
  --resolution 1280x720 --speed QUALITY \
  --output projects/NAME/out/thumbnail.png --json-out
```

`--resolution 1280x720` is YouTube's recommended size, and Ideogram 4 returns it exactly,
so no resize is needed. Parse the JSON line: `success` must be `true`.

For variations, write `caption-2.json`, `caption-3.json` with a different phrase or layout,
and output `thumbnail/thumbnail-2.png` and so on. Then copy the one the user picks to
`out/thumbnail.png`.

### Step 6: Check it

**Read the PNG and look at it.** Check:
- Every word is spelled exactly as in the caption. Look for missing, doubled or extra
  letters, and stray filler text
- The text is readable at small size, with no important element in the bottom-right corner
- The colours match the brand

If the text is wrong, regenerate once. Each run uses a new random seed, so a second
attempt may get it right. If it fails again, shorten the phrase or simplify the `desc`, then
retry. Show the user the result and ask before spending on further retries.

Then confirm it fits YouTube's limits (≤2MB, 1280×720):

```bash
cd /path/to/claude-code-video-toolkit && uv run python -c "import sys,os; from PIL import Image; p=sys.argv[1]; print(Image.open(p).size, os.path.getsize(p)//1024, 'KB')" projects/NAME/out/thumbnail.png
```

A flat 1280×720 graphic is usually 0.5–1MB. If it's over 2MB, convert it to JPEG and use
that file instead:

```bash
ffmpeg -y -i projects/NAME/out/thumbnail.png -q:v 3 projects/NAME/out/thumbnail.jpg
```

### Step 7: Write back and report

Merge into `project.json`, keeping every other field:

```json
"publish": { "thumbnail": "out/thumbnail.png" },
"thumbnail": {
  "phrase": "SCREEN SHARE",
  "caption": "thumbnail/caption.json",
  "model": "ideogram-4",
  "generatedAt": "<today ISO date>"
}
```

Set `publish.thumbnail` only. Don't create or overwrite other `publish` fields. `/publish`
reads them as defaults. Append a `sessions[]` entry, then report:

```
Thumbnail ready

File:    projects/NAME/out/thumbnail.png  (1280×720, 650 KB)
Phrase:  SCREEN SHARE
Cost:    ~$0.10 (1 image)

Next: /publish NAME (it will pick this up as the thumbnail)
```

---

## Quick Mode

```
/thumbnail android-screenshare-sprint
/thumbnail android-screenshare-sprint "SCREEN SHARE"
```

With a phrase, skip Step 3. Still check the generated text (Step 6) before reporting.

---

## Notes

- **Not for Remotion title cards.** Use a FLUX.2 background with Remotion text for slides
  that animate (see CLAUDE.md, "FLUX.2 vs Ideogram 4"). A thumbnail is a static image, so
  it's the case where baked-in text is the right choice.
- **Ideogram 4.5** (`--model 4.5`) can't take `1280x720`, because its sides must be
  multiples of 32. Use `--resolution 2560x1440`, then downscale with
  `ffmpeg -i in.png -vf scale=1280:720 out.png`. Stay on Ideogram 4 unless the user asks.
- Custom thumbnails on YouTube need a channel with a verified phone number. `/publish`
  reports it if the thumbnail was not set.

---

## Evolution

This command evolves through use. If something's awkward or missing:
1. Say "improve this" → Claude captures it in `_internal/BACKLOG.md`
2. Edit `.claude/commands/thumbnail.md` → update `_internal/CHANGELOG.md`
- Issues/PRs: `github.com/digitalsamba/claude-code-video-toolkit`
