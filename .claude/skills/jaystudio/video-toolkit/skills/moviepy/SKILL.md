---
name: moviepy
description: Python video composition with moviepy 2.x — overlaying deterministic text on AI-generated video (LTX-2, SadTalker), compositing clips, single-file build.py video projects. Use when adding labels/captions/lower-thirds to LTX-2 or SadTalker outputs, building short ad-style spots in pure Python without Remotion, or doing programmatic video composition. Triggers include text overlay on video, label LTX-2 clip, caption SadTalker output, lower third, build.py video, moviepy, Python video composition, sub-30s ad spot.
---

# moviepy for Video Production

moviepy is the toolkit's go-to library for **putting deterministic text on top of AI-generated video** and for building short, single-file Python video projects without a Remotion toolchain.

The deeper principle is **trustworthy text**: any genre where text *has to* be readable, accurate, and consistent (legally, editorially, or commercially) is a genre where AI-rendered in-frame text is unacceptable and a moviepy overlay step is the natural fix. Names must be spelled right. Prices must be exact. Source attributions must be pixel-perfect. AI generation models cannot guarantee any of that.

## When to use moviepy vs. Remotion

| Use moviepy when… | Use Remotion when… |
|-------------------|---------------------|
| Overlaying text/labels on an LTX-2 or SadTalker output | Building long-form sprint reviews or product demos |
| Building sub-30s ad-style spots in a single `build.py` | Multi-template, multi-brand, design-heavy work |
| Compositing data-driven visuals (matplotlib `FuncAnimation` → mp4) | Anything needing React components or design system reuse |
| One-off transformations on existing video files | Anything where the project lifecycle (planning → render) matters |
| You want zero Node.js / no React mental overhead | You want hot-reload preview in Remotion Studio |

Two runnable references for everything in this skill live in `examples/`:

- **`examples/quick-spot/build.py`** — 15-second ad-style spot. Audio-anchored timeline, text overlay, optional VO + ducked music. Renders silent out of the box with zero external assets.
- **`examples/data-viz-chart/build.py`** — animated time-series chart with deterministic title and source attribution. Demonstrates the matplotlib (data) + moviepy (trustworthy text) split.

Both run with `uv run build.py` and produce a real `out.mp4` immediately. Read them alongside this skill — every pattern below is shown working there.

**Dependencies.** `moviepy`, `Pillow`, and `matplotlib` are declared in the root `pyproject.toml` and installed with the toolkit's one-line Python setup: `uv sync`. If you hit `Missing dependency` when running an example, run that command from the repo root — the examples' `build.py` files will tell you the same thing in their error message and exit cleanly rather than printing a bare traceback.

## The main use case: text on AI-generated video

Both LTX-2 and SadTalker output bare visuals:

- **LTX-2** cannot reliably render readable text (the model hallucinates letterforms — see the ltx2 skill's "Bad Prompts").
- **SadTalker** outputs a talking head with no captions, labels, lower thirds, or context.

The fix is to generate the visual cleanly, then composite text over it deterministically with moviepy. This is the canonical pattern in this toolkit:

```python
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

# 1. AI-generated visual (LTX-2 or SadTalker output)
bg = VideoFileClip("lugh_ltx.mp4").without_audio()

# 2. Text rendered via PIL → ImageClip (see "Text rendering" below)
title = (
    ImageClip("text_cache/intro_title.png")
    .with_duration(2.0)
    .with_start(0.5)
    .with_position(("center", 880))
)

# 3. Composite
final = CompositeVideoClip([bg, title], size=(1920, 1080))
final.write_videofile("lugh_with_caption.mp4", fps=30, codec="libx264")
```

Common shapes this takes:

| Shape | LTX-2 use | SadTalker use |
|-------|-----------|---------------|
| Title card over hero footage | "INTRODUCING LONGARM" over a cinematic LTX-2 b-roll | n/a |
| Lower third / name plate | n/a | "Lugh — Ancient Warrior God" under a talking head |
| Quote caption | "I am going home." over an LTX-2 character cameo | Same, over a SadTalker talking head |
| Brand attribution | Logo + URL fade-in over the last second | Same |
| Tinted overlay for contrast | Dark navy semi-transparent layer behind text | Same |

## Genres where this shines

The "AI-visual + deterministic text overlay" pattern is the natural production pipeline for several styles of video. If the request matches one of these, reach for moviepy by default:

| Genre | What you overlay | Why moviepy is the right call |
|-------|------------------|-------------------------------|
| **News / talking-head journalism** | Speaker name plates, location bars, breaking-news banners, source attribution, pull quotes | Names must be spelled right (editorial / legal). The biggest category by volume. |
| **Documentary segments** | Interviewee lower thirds, chapter titles, archival source credits, location stamps | Same trust requirement as news. |
| **Trailers / promo spots** | Title cards, credit overlays ("FROM THE DIRECTOR OF…"), date stings, quote cards, CTAs | Tightly timed, text-heavy, every frame matters. The `q2-townhall-longarm-ad` example is exactly this. |
| **Social short-form (Reels, TikTok, Shorts)** | Word-accurate captions for sound-off viewing, hashtag overlays | Most social viewing is muted; captions are non-negotiable. |
| **Product demos with annotations** | Pricing callouts, feature labels, "click here" pointers over screen recordings, before/after labels | Prices and product names must be exact. |
| **Tutorials / explainers** | Step number overlays, terminal-command captions, keyboard-shortcut callouts | Step numbers must be sequential, commands must be copy-pasteable. |

Lesser-but-real fits: music videos (lyric overlays), reaction videos (source attribution), sports recaps (score overlays), real-estate tours (price / sqft), conference talks (speaker + session plate).

**For full SRT-driven subtitling** (long-form, time-coded, multilingual) moviepy is workable but not ideal — reach for `ffmpeg` with `subtitles` filter or a dedicated subtitle tool. moviepy is best for hand-placed overlays, not bulk caption tracks.

## Text rendering — use PIL, not `TextClip`

**Critical gotcha:** moviepy 2.x's `TextClip(method='label')` has a tight-bbox bug that **clips letter ascenders and descenders** (the tops of capitals, the tails of g/p/y). On Apple Silicon you'll see characters with sliced edges and not realise what's wrong for hours.

**The workaround:** render text to a transparent PNG via PIL, then load it as an `ImageClip`. Cache the result by content hash so re-builds are free.

```python
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

def render_text_png(txt, size, hex_color, cache_dir="./text_cache"):
    cache = Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{txt}|{size}|{hex_color}".encode()).hexdigest()[:16]
    path = cache / f"{key}.png"
    if path.exists():
        return str(path)

    font = ImageFont.truetype(ARIAL_BOLD, size)
    bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = max(20, size // 4)

    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    rgb = tuple(int(hex_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    ImageDraw.Draw(img).text((pad - bbox[0], pad - bbox[1]), txt, font=font, fill=(*rgb, 255))
    img.save(path)
    return str(path)
```

The full helper (with kwargs for bold, position, fades, and cleaner ergonomics) is in `examples/quick-spot/build.py` — copy it rather than re-implementing.

## Audio-anchored timeline pattern

For ad-style edits where every frame matters, generate per-scene VO first and anchor every visual to known absolute timestamps. This eliminates timing drift entirely. See **CLAUDE.md → Video Timing → Audio-Anchored Timelines** for the full pattern. The short version:

```python
# Audio-anchored timeline (25s):
#   Scene 1 tired      0.3 → 3.74  (audio 3.44s)
#   Scene 2 worries    4.0 → 8.88  (audio 4.88s)

text_clip("TIRED OF",     start=0.5,  duration=1.2)
text_clip("THIRD-PARTY",  start=1.0,  duration=1.8)
vo_clip("01_tired.mp3",   start=0.3)
vo_clip("02_worries.mp3", start=4.0)
```

## Common recipes

### Text on a single AI-generated clip

```python
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

bg = VideoFileClip("ltx_hero.mp4").without_audio()
caption = (
    ImageClip(render_text_png("THE FUTURE OF AGENTS", 140, "#FFFFFF"))
    .with_duration(bg.duration)
    .with_position(("center", 880))
)
CompositeVideoClip([bg, caption], size=bg.size).write_videofile("captioned.mp4", fps=30)
```

### Lower third over a SadTalker talking head

```python
from moviepy import VideoFileClip, ImageClip, ColorClip, CompositeVideoClip

talking = VideoFileClip("narrator_sadtalker.mp4")
W, H = talking.size

# Semi-transparent bar across the bottom for contrast
bar = (
    ColorClip((W, 140), color=(20, 24, 38))
    .with_duration(talking.duration)
    .with_opacity(0.75)
    .with_position(("center", H - 160))
)
name = (
    ImageClip(render_text_png("LUGH", 72, "#F06859"))
    .with_duration(talking.duration)
    .with_position((80, H - 150))
)
title = (
    ImageClip(render_text_png("Ancient Warrior God", 36, "#FFFFFF"))
    .with_duration(talking.duration)
    .with_position((80, H - 80))
)
CompositeVideoClip([talking, bar, name, title]).write_videofile("with_lower_third.mp4", fps=30)
```

### Tinted overlay for text contrast over busy footage

LTX-2 b-roll is often too visually busy for legible text. Drop a semi-transparent navy layer between the video and the text:

```python
from moviepy import ColorClip

tint = (
    ColorClip((W, H), color=(20, 24, 38))
    .with_duration(duration)
    .with_opacity(0.55)
)
# Composite order: bg → tint → text
CompositeVideoClip([bg, tint, text_clip])
```

### Side-by-side composite

```python
from moviepy import VideoFileClip, CompositeVideoClip, ColorClip

left  = VideoFileClip("demo_a.mp4").resized(width=960).with_position((  0, "center"))
right = VideoFileClip("demo_b.mp4").resized(width=960).with_position((960, "center"))
bg    = ColorClip((1920, 1080), color=(0, 0, 0)).with_duration(max(left.duration, right.duration))
CompositeVideoClip([bg, left, right]).write_videofile("split.mp4", fps=30)
```

### Mix per-scene VO with ducked music

```python
from moviepy import AudioFileClip, CompositeAudioClip
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
from moviepy.audio.fx.AudioFadeOut import AudioFadeOut

music = AudioFileClip("music.mp3").with_effects([
    MultiplyVolume(0.22),  # duck under VO
    AudioFadeIn(0.5),
    AudioFadeOut(1.5),
])
vo = [
    AudioFileClip(f"scenes/0{i}.mp3").with_effects([MultiplyVolume(1.15)]).with_start(start)
    for i, start in [(1, 0.3), (2, 4.0), (3, 9.1)]
]
final_audio = CompositeAudioClip([music] + vo)
```

## Gotchas

- **moviepy 2.x renamed methods.** Use `subclipped` (not `subclip`), `with_duration` / `with_start` / `with_position` (not `set_duration` etc.), `with_effects([...])` instead of `.fadein()`/`.fadeout()`. Many tutorials online still show 1.x syntax — be skeptical.
- **`TextClip(method='label')` clips ascenders/descenders.** Always use the PIL workaround above.
- **`OffthreadVideo` is Remotion-only.** moviepy uses `VideoFileClip`. Don't mix the two.
- **Resizing requires Pillow ≥ 10.0** for the LANCZOS resample. If you see `ANTIALIAS` errors, upgrade Pillow.
- **`ColorClip` takes RGB tuples, not hex strings.** Use `(20, 24, 38)`, not `"#141826"`.
- **Audio in `VideoFileClip` is loaded by default.** Call `.without_audio()` if you only want the visual — composing with audio you don't want will cause silent VO drops in `CompositeAudioClip`.
- **Always set `size=(W, H)` on `CompositeVideoClip`.** Without it, output dimensions follow the first clip, which can be smaller than your target.

## When to reach for what

| Task | Tool |
|------|------|
| Animate a still image | `tools/ltx2.py --input` |
| Talking head from photoreal portrait | `tools/sadtalker.py` |
| Talking head from stylized character | `tools/ltx2.py --input` (see ltx2 skill) |
| **Add a label/caption/lower third to either of the above** | **moviepy + PIL (this skill)** |
| Convert / compress / resize an existing file | `ffmpeg` (see ffmpeg skill) |
| Long-form, design-system-driven video | Remotion (see remotion skill) |

## References

- Runnable example — short ad-style spot: `examples/quick-spot/build.py`
- Runnable example — data-viz with text overlay: `examples/data-viz-chart/build.py`
- Audio-anchored timelines: `CLAUDE.md → Video Timing → Audio-Anchored Timelines`
- Related skills: `ltx2`, `ffmpeg`, `remotion`
