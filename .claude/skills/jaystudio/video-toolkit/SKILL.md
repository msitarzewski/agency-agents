---
name: video_toolkit
description: Make short explainer videos from a brief with claude-code-video-toolkit — submit a scene spec, poll a job, get a QC-checked MP4. Also covers the individual tools (AI voiceover, images, clips, music, talking heads) for custom work.
metadata:
  openclaw:
    emoji: "🎬"
    skillKey: "video-toolkit"
    os: ["darwin", "linux", "win32"]
    requires:
      bins: ["uv", "ffmpeg"]
---

# Video Toolkit

Turn a brief into a finished MP4 with [claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit).
This skill is written for **any agent runtime**: Claude Code, OpenClaw, Codex, Hermes, a bare API loop with a
`run_tool` call, or an MCP client. Nothing here depends on how your runtime backgrounds work, because the long
work runs in a detached job you poll.

## Where the toolkit is

Every command below runs **from the toolkit root**. Find it, in this order:

1. `$VIDEO_TOOLKIT_ROOT` if set (also honoured by the toolkit's own scripts);
2. `$VIDEO_TOOLKIT_DIR` (the name longarm uses);
3. a `claude-code-video-toolkit/` directory under your workspace or home.

```bash
cd "${VIDEO_TOOLKIT_ROOT:-${VIDEO_TOOLKIT_DIR:-$HOME/claude-code-video-toolkit}}"
uv run tools/verify_setup.py --json     # prerequisites, keys and endpoints; [x] means ready
```

Never run a tool from inside a project directory: tools resolve paths relative to the toolkit root. If your
runtime can't `cd`, pass `--directory`: `uv run --directory /path/to/toolkit tools/video_job.py ...`.

**No shell at all?** Use the MCP server instead: `uv run --directory /path/to/toolkit --extra mcp tools/video_mcp.py`
exposes `video_estimate`, `video_submit`, `video_status`, `video_result` and `video_list_presets` over stdio.
Same flow as below, same JSON.

## The quick path: estimate → submit → poll → result

`tools/video_job.py` is one async entrypoint. `submit` returns in seconds with a job id; a detached worker runs
the whole pipeline (voiceover → visuals → captions → build → QC); every later call is short and reads state
from disk. That is how it fits a per-call time limit, and it survives you going away between turns.

### 1. Write the spec (you are the LLM)

A spec is a list of scenes, each with narration text and one visual. Budget about 2.4 words a second of
narration; a 45 s video is ~100 words in 3 to 5 scenes.

```json
{
  "title": "Why do we have leap years?",
  "format": "9:16",
  "voice": {"provider": "qwen3", "speaker": "Ryan", "tone": "warm", "maxWpm": 165},
  "scenes": [
    {"slug": "hook",
     "text": "Every four years, February gets an extra day. Why? Because a year isn't 365 days long.",
     "visual": {"kind": "ltx", "prompt": "Slow orbital shot of Earth turning in space, sunlight sweeping the oceans, cinematic, no text"}},
    {"slug": "quarter",
     "text": "Earth takes about 365 and a quarter days to orbit the sun. Ignore the quarter and the calendar drifts.",
     "visual": {"kind": "ideogram", "caption": { "...filled from the caption template below..." }}},
    {"slug": "cta",
     "text": "So every fourth year we add one day back. Follow for one concept a week.",
     "visual": {"kind": "ideogram", "caption": { "...filled from the caption template below..." }}}
  ]
}
```

- `format`: `9:16` (Shorts, Reels, TikTok) or `16:9` (YouTube, decks).
- `visual.kind`: `ltx` (5 s motion b-roll, prompt the motion and atmosphere, never on-screen text),
  `text` (constructed: a generated background that drifts, with `headline` and optional `subline`
  animated in; about a cent), `ideogram` (a designed card with legible text: **always a `caption`
  object**, filled from the template below), `flux` (text-free generated background), `none`
  (placeholder, drafts only). A scene with no visual gets a generated background. Alternate motion
  and constructed scenes so there is a pattern interrupt every ~15 s.
- `voice`: a preset name (`"lugh"`, from `assets/voices/lugh.json`) or an object. The title animates
  over the first scene and a soft music bed is mixed in by default; `"titleCard": false` and
  `"music": false` turn them off.
- **No JSON at all:** `--scene "narration :: ltx: motion prompt"` per scene, `--scene "narration ::
  text: HEADLINE ; subline"`, `--title`, `--voice lugh`. See the docs page for the full flat form.
- Scene 1 must hook in one sentence. Scene N is the call to action. Captions are burned from the script text,
  so write every scene exactly as it should appear.
- Optional: `"music": {"enabled": true, "prompt": "..."}` (off by default), `"brand": "digital-samba"`,
  `"ideogram": {"speed": "TURBO"}` to halve image cost, `"captions": {"enabled": false}`.
- `uv run tools/video_job.py presets` prints the full price table, formats and an example spec.

#### The caption template (every `ideogram` scene)

Ideogram renders text reliably only from a structured JSON caption. A plain `prompt` works but adds small
filler text to the card ("A REMINDER", a fake tagline), so fill this in instead. Replace the `<...>`
placeholders and leave everything else. The headline is under 6 words, all caps. `bbox` is
`[top, left, bottom, right]` on a 0 to 1000 grid, so the same numbers work for 9:16 and 16:9.
`uv run tools/video_job.py presets --json` prints it as `ideogram_caption_template`.

```json
{
  "high_level_description": "A <dark-navy poster> with the headline <HEADLINE>, showing <one simple diagram or icon>, with clear space in the bottom fifth of the frame.",
  "style_description": {
    "aesthetics": "clean, diagrammatic, modern explainer",
    "lighting": "flat even lighting, soft glow on the main object",
    "medium": "flat vector graphic design",
    "art_style": "minimalist infographic poster, generous negative space",
    "color_palette": ["#0A1428", "#4DA8FF", "#FFB347", "#FFFFFF"]
  },
  "compositional_deconstruction": {
    "background": "Deep navy gradient, faint tiny stars.",
    "elements": [
      {"type": "text", "bbox": [80, 80, 200, 920], "text": "<HEADLINE>",
       "desc": "Bold condensed sans-serif headline, all caps, white, centered at the top.",
       "color_palette": ["#FFFFFF"]},
      {"type": "obj", "bbox": [280, 150, 760, 850],
       "desc": "<One object: what it is, its shape, its colour. No text on it.>",
       "color_palette": ["#4DA8FF", "#FFB347"]}
    ]
  }
}
```

Rules of thumb: one headline and one object per card; describe the object as shapes and colours, not as a
concept (for a diagram, write the object as a chain, `"object": "prompt -> agent -> video"`, and the toolkit
lays out labelled boxes and arrows); keep the bottom fifth empty because the burned captions sit there; change `color_palette` only
when the brand asks for it. The full caption format, for cards with more elements, is in the toolkit's
`.claude/skills/ideogram4/`.

Have only a brief and want the toolkit to write the spec? Set `VIDEO_JOB_EXPANDER` to any command that reads
`{"brief","format","duration_s",...}` on stdin and prints a spec JSON (`claude -p`, a curl to any model, your own
script). Then `--brief "..."` works everywhere `--spec` does. Without it, `estimate --brief` still answers with a
skeleton estimate; `submit --brief` is refused.

Runtimes that pass an argv list and can't write files (longarm's `native__run_tool`, most MCP
bridges) take the spec inline: `--spec-json '<json>'`, with the short caption form
`{"headline": "...", "object": "...", "description": "..."}` per ideogram scene so it fits in one
argument. Add `--output files/<dated-name>.mp4` when your runtime serves a `files/` directory at
a public URL; the file lands there once the job is done.

### 2. Estimate, then submit under a cap

```bash
uv run tools/video_job.py estimate --spec spec.json --json
# {"estimate_usd": 0.35, "breakdown": [...], "scenes": 3, "video_s_approx": 31.0, ...}

uv run tools/video_job.py submit --spec spec.json --max-usd 1.00 --json
# {"id": "20261031-230304-f34a", "phase": "queued", "estimate_usd": 0.353, "poll": "..."}
```

`submit` is refused (exit 2, `error_code: budget_exceeded`) when the estimate is over `--max-usd`, before any
spend. Only one job runs at a time: a second `submit` while one is running exits 3 with `error_code: lock_held`
and the running job's id. The worker also stops itself before the next paid step if actual spend would pass the
cap.

### 3. Poll status

```bash
uv run tools/video_job.py status JOB_ID --json
```

Poll every 20 to 30 s. `phase` walks `queued → voiceover → visuals → captions → build → qc → publish → done`,
or ends in `failed` (with `error` and `error_code`) or `cancelled`. `progress` is 0 to 100, `eta_s` is a rough
seconds-left figure (say "about 3 minutes to go", not a percentage), `actual_usd` is spend so far,
`step_detail` names the asset being generated, `events` is a timestamped list of what started and finished
(each scene voiced with its wpm, each clip or image made with its seconds and cost, QC, the render size), and
`log_tail` is the last few log lines. Use the last two or three `events` to say what is happening ("two images
done, the clip for scene 3 is rendering") rather than naming a phase. `eta_s` is calibrated from this host's
recent jobs. A typical 30 s video takes 5 to 10 minutes; the LTX clip is the slow step (2 to 4 minutes each,
more on a cold start).

Tell the user the id and the estimate as soon as `submit` returns. Do not promise to keep watching from inside
one turn: the job carries on without you, and `status` works from any fresh process. If your runtime has a
scheduler or a poller, point it at `status`; otherwise check when you are next invoked.

### 4. Collect the result

```bash
uv run tools/video_job.py result JOB_ID --json
# {"ready": true, "mp4": "/.../jobs/20261031-230304-f34a/why-do-we-have-leap-years-9x16.mp4",
#  "url": "https://...r2...", "duration_s": 31.4, "qc": {"passed": true, "errors": 0, "warnings": 1}, "actual_usd": 0.39}
```

`url` is a 2 h presigned download link when Cloudflare R2 is configured, otherwise null and you deliver the
file. `qc` is `tools/qc.py --render`: loudness was normalised to -14 LUFS, and it reports still stretches,
black gaps and a silent track. Pass `qc.warnings` on to the user in a line; `qc.errors > 0` means look before
you ship. `warnings` (a list of sentences) is for the user too: captions or music skipped, a scene voiced too
fast, a file over the size cap. Exit 2 means not ready yet. The MP4 is encoded under 9.5 MB so it attaches in
chat (Discord's bot limit is 10 MB); `maxMB: 0` in the spec turns that off for a full-quality YouTube upload.

If a job ends `failed` or `cancelled` with `resumable: true`, run `resume JOB_ID` (add `--max-usd` after a
`budget_exceeded` stop) rather than submitting again: it keeps the voice, visuals, captions and music already
paid for and redoes only what is missing.

Also: `list --json` (recent jobs), `cancel JOB_ID`, `prune` (old jobs' project trees; `submit` does this
itself), and every job keeps `jobs/<id>/job.log`, `receipts.jsonl`
(one JSON line per paid call: `ts, tool, cost_usd, elapsed_s, exit, args, job_id`) and the project copy it
rendered from, so a human can open `jobs/<id>/project/` and re-render after edits.

### Spend

Receipts also append to `MEDIA_SPEND_LOG` (default `logs/media-spend.log` in the toolkit) in the same shape
longarm's `video-spend.py` writes, so one ledger covers single assets and jobs. Prices (`presets`, checked
against receipts on 2026-11-01): LTX clip ~$0.10, Ideogram image $0.03 to $0.10, FLUX image under a cent,
Qwen3 voice ~$0.01 a scene, captions ~$0.0001 a second. A 7-scene, 45 s video with two clips and two cards
lands around $0.40 to $0.55; the first clip after idle pays a Modal cold start on top. Under `--progress json`
every call prints one `cost` event, failures included ($0).

---

## Deeper: the individual tools

Everything below is what `video_job.py` drives for you. Reach for it directly when the user wants one asset
(an image, a clip, a song), a different template, or a talking head. Add `--progress json` to any cloud tool
for JSON-lines progress on stderr, and `--json` for a machine-readable result on stdout.

### Defaults that are current (2026-10-31)

| Need | Use | Not |
|---|---|---|
| Legible text in an image (title card, thumbnail, quote card) | `ideogram4.py --json caption.json` | FLUX or LTX (both garble text) |
| Text-free background for an overlay | `flux2.py --preset title-bg` | |
| Motion b-roll, animate a still | `ltx2.py` (`--input` for image-to-video) | |
| Voiceover | `voiceover.py --provider qwen3 --cloud modal --max-wpm 165` (free, self-hosted) or `--provider elevenlabs` | |
| Talking head anyone will watch | `soulx.py` (SoulX-FlashHead Pro, Modal only) | `sadtalker.py` is drafts, or when Modal is down |
| Music | `music_gen.py --preset corporate-bg` (acemusic key, free) | |
| Before delivering any render | `qc.py --render out.mp4 --fix` | shipping unchecked |
| Captions for a Remotion template | `captions.py public/audio/scenes` | burning the recogniser's own transcript |
| Social cut-downs of a 16:9 render | `cutdown.py --input out.mp4 --platform shorts` | |

### Voiceover

```bash
uv run tools/voiceover.py --provider qwen3 --cloud modal --scene-dir public/audio/scenes --max-wpm 165 --json
uv run tools/qwen3_tts.py --text "Hello" --speaker Ryan --tone warm --output hello.mp3 --cloud modal
uv run tools/qwen3_tts.py --text "Hello" --ref-audio ref.wav --ref-text "exact transcript" --output clone.mp3 --cloud modal
```

One `.txt` per scene in `--scene-dir`, one MP3 back per scene with `duration_seconds`, `wpm` and a `pacing`
label. `--max-wpm 165` slows rushed takes with pitch-preserving atempo; a cloned voice copies its reference
clip's pace, so a flat or fast clone needs a better reference (`voice_prosody.py expand`), not a higher
temperature. Speakers: Ryan, Aiden, Vivian, Serena, Uncle_Fu, Dylan, Eric, Ono_Anna, Sohee. Tones: neutral,
warm, professional, excited, calm, serious, storyteller, tutorial.

### Images

```bash
# Text in the image: author the caption JSON yourself (see .claude/skills/ideogram4/), 9:16 = 1440x2560, 16:9 = 1280x720
uv run tools/ideogram4.py --json caption.json --resolution 1440x2560 --output card.png
# Text-free background
uv run tools/flux2.py --preset title-bg --brand digital-samba --output bg.png --cloud modal --progress json
# Edit a photo, upscale
uv run tools/image_edit.py --input photo.jpg --prompt "Add sunglasses" --cloud modal
uv run tools/upscale.py --input small.png --scale 4 --cloud modal
```

### Video clips

```bash
uv run tools/ltx2.py --prompt "Aerial over a city at golden hour, cinematic" --width 1024 --height 576 \
    --num-frames 121 --output broll.mp4 --no-open --progress json --json
uv run tools/ltx2.py --prompt "Gentle camera drift, soft light shifts" --input still.png --output animated.mp4 --no-open
```

Sides must be multiples of 64; frames satisfy (n-1) % 8 == 0 (121 ≈ 5 s, 161 ≈ 7 s). About $0.07 to $0.20 a
clip and 2 to 4 minutes; the first clip after idle adds a cold start. Prompt motion and atmosphere, never text.
Add `--negative-prompt "anime, cartoon, watermark, text, logo"` when style drifts. `chain_video.py` chains
clips for continuity (one command, per-scene prompts in a JSON file).

### Talking heads

```bash
uv run tools/soulx.py --image presenter_16x9.png --audio scene01.mp3 --size 768 --output narrator01.mp4
uv run tools/soulx.py --image presenter_16x9.png --audio scene01.mp3 --model lite --width 512 --height 288 --output draft.mp4
```

SoulX follows the image's aspect ratio and holds identity over long takes (97% of frame-zero sharpness at
70 s). Pick one resolution per project: `torch.compile` recompiles on every size change (~10 min cold). Pro
sides are multiples of 16, Lite multiples of 32. SadTalker (`--preprocess full --still --expression-scale 0.8`)
is the RunPod fallback and square by default. Don't grade talking heads with a similarity metric; look at a
contact sheet.

### Music

```bash
uv run tools/music_gen.py --preset corporate-bg --duration 60 --output bg.mp3 --progress json
uv run tools/music_gen.py --prompt "lofi, warm keys, no vocals" --duration 45 --variations 3 --output bg.mp3
uv run tools/pick_music.py bg_*.mp3 --target 45 --under voice --pick bg.mp3 --json   # takes the best, says why
```

Presets: corporate-bg, upbeat-tech, ambient, dramatic, tension, hopeful, cta, lofi. Default provider is the
acemusic API (free key); `--cloud modal` is the self-hosted fallback.

### QC, captions, cut-downs

```bash
uv run tools/qc.py --project projects/my-video                  # assets, timing, pacing, loudness
uv run tools/qc.py --render out/video.mp4 --fix                  # -14 LUFS, writes video.loudnorm.mp4; frame checks
uv run tools/captions.py projects/my-video/public/audio/scenes  # word captions aligned to the script .txt
uv run tools/cutdown.py --input out/video.mp4 --platform shorts  # 16:9 -> 9:16, blur-fit
```

Run `qc.py --render` before every delivery: the templates mix voice and music without normalising, and
YouTube turns quiet audio down, never up. It exits 1 on errors (cut-off narration, silent track).

### Remotion templates (when a job's compositor isn't enough)

`templates/product-demo` (marketing), `templates/sprint-review` and `sprint-review-v2`,
`templates/ds-release-notes` (synthetic UI demos). Copy to `projects/<name>`, `npm install`, write the config,
generate per-scene audio, update each scene's `durationSeconds` to `ceil(audio + 2)` (or run
`uv run tools/sync_timing.py --apply`), `npm run render` from the project directory, then `qc.py --render`.
Always `<OffthreadVideo>` and `<Audio>` from `remotion`, never a raw `<video>` tag. The toolkit's CLAUDE.md
holds the full workflow.

### Progress JSON (stderr, one object per line)

```json
{"ts":"14:23:15","stage":"submit","msg":"Sending to Modal...","pct":null,"elapsed":0.0}
{"ts":"14:24:02","stage":"complete","msg":"Saved: clip.mp4","pct":100,"elapsed":47.3}
{"ts":"14:24:02","stage":"cost","msg":"Est. cost: $0.0712 (103s on modal)","pct":null,"elapsed":103.0}
```

Stages: `submit`, `queue`, `processing`, `waiting`, `item` (n of m, `pct` set), `cost`, `complete`, `error`.
`video_job.py` reads the `cost` events for its receipts; longarm's `video-spend.py` wrapper does the same for
single tool runs.

## Error recovery

| Problem | Fix |
|---|---|
| `No module named ...` | `uv sync` from the toolkit root, run tools with `uv run` |
| `MODAL_*_ENDPOINT_URL not configured` | `uv run tools/verify_setup.py`; `uv run tools/modal_setup.py --list` |
| `submit` exits 3, `lock_held` | Another job is running; `status` that id, or `cancel` it if it is stuck |
| `submit` exits 2, `budget_exceeded` | Raise `--max-usd`, drop a scene, use `flux` or `"ideogram": {"speed": "TURBO"}` |
| `submit --brief` exits 2, `no_expander` | Write the spec yourself and pass `--spec`, or set `VIDEO_JOB_EXPANDER` |
| Job `failed`, `error_code: step_failed` | `status --json` has the error; `jobs/<id>/job.log` has the tool output. Modal cold starts can time out once: `resume JOB_ID` |
| Job `failed`, `worker_died` or `worker_never_started` | The worker was killed (a container restart, say). `resume JOB_ID`: it reuses everything already made |
| Cold start on Modal | First call after idle takes 1 to 3 minutes; the next is warm |
| Captions missing from a job's video | No `ELEVENLABS_API_KEY` and no local whisper (`uv sync --extra whisper`); the job renders without and says so in `warnings` |
