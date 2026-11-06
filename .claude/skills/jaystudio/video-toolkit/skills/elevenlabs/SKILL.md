---
name: elevenlabs
description: Generate AI voiceovers, sound effects, and music using ElevenLabs APIs. Use when creating audio content for videos, podcasts, or games. Triggers include generating voiceovers, narration, dialogue, sound effects from descriptions, background music, soundtrack generation, voice cloning, or any audio synthesis task.
---

# ElevenLabs Audio Generation

Requires `ELEVENLABS_API_KEY` in `.env`.

## Text-to-Speech

```python
from elevenlabs.client import ElevenLabs
from elevenlabs import save, VoiceSettings
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

audio = client.text_to_speech.convert(
    text="Welcome to my video!",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    voice_settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
        style=0.5,
        speed=1.0
    )
)
save(audio, "voiceover.mp3")
```

### Models

| Model | Quality | SSML Support | Notes |
|-------|---------|--------------|-------|
| `eleven_multilingual_v2` | Highest consistency | None | Stable, production-ready, 29 languages. Toolkit default; supports style + speed |
| `eleven_v4` | Most expressive | None (audio tags, IPA) | Newest (released 2026-09-28), 90+ languages, best clone accuracy. Stability + similarity only, no style/speed |
| `eleven_flash_v2_5` | Good | `<break>`, `<phoneme>` | Fastest, cheapest; supports pause/pronunciation tags |
| `eleven_v3` | Expressive | None | Previous generation — prefer v4 |

**Choose:** multilingual_v2 for reliability and speed/style control, v4 for maximum expressiveness and cloned voices (test a few takes), flash for SSML control.

**Deprecated:** `eleven_turbo_v2_5` → use `eleven_flash_v2_5` (same quality, lower latency; see [deprecated models](https://elevenlabs.io/docs/overview/models#deprecated-models)). The toolkit still accepts `--model eleven_turbo_v2_5`: it prints a one-line warning and sends `eleven_flash_v2_5`.

### Eleven v4

Released 2026-09-28 ([changelog](https://elevenlabs.io/docs/changelog/2026/9/28), [model page](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4#model-variants)). The toolkit calls v4 through the **Text to Dialogue** API with one input (the narrator voice), as ElevenLabs recommends for content creation and long-form audio:

```python
from elevenlabs import DialogueInput

audio = client.text_to_dialogue.convert(
    inputs=[DialogueInput(text="[warm] Welcome to my video!", voice_id="JBFqnCBsd6RMkjVDRZzb")],
    model_id="eleven_v4",
    settings={"stability": 0.5, "similarity": 0.75},  # the only two settings v4 takes
)
save(audio, "voiceover.mp3")
```

- `uv run tools/voiceover.py --model eleven_v4 ...` (and `redub.py --model eleven_v4`) do this for you, warn once that `--style`/`--speed` are ignored, and split text over ~2,000 chars per request (the reliable dialogue limit) at sentence boundaries. Pace with `--max-wpm` instead of `--speed`.
- `client.text_to_dialogue.convert_with_timestamps(...)` returns the same character alignment as TTS `convert_with_timestamps`, so `redub.py --sync` works with v4 and sends the same stability + similarity.
- Pass `settings` as a dict: SDK versions before 2.69 type it with a stability-only model. The API reads `similarity` there since 2026-09-28 (it rejects an out-of-range value with a 422). Text to Dialogue needs `elevenlabs>=2.21`.
- Direct delivery with audio tags (`[whispering]`, `[warm]`, `[sigh]`) and punctuation. Write tags that clearly describe the voice, because v4 can also read a tag as a sound effect.
- `eleven_v4_turbo` is the real-time variant, available only over the Text to Dialogue WebSocket. The toolkit doesn't use it, since offline renders don't benefit from low latency.

### Voice Settings by Style

| Style | stability | similarity | style | speed |
|-------|-----------|------------|-------|-------|
| Natural/professional | 0.75-0.85 | 0.9 | 0.0-0.1 | 1.0 |
| Conversational | 0.5-0.6 | 0.85 | 0.3-0.4 | 0.9-1.0 |
| Energetic/YouTuber | 0.3-0.5 | 0.75 | 0.5-0.7 | 1.0-1.1 |

### Pauses Between Sections

**With flash models:** Use SSML break tags inline:
```
...end of section. <break time="1.5s" /> Start of next...
```
Max 3 seconds per break. Excessive breaks can cause speed artifacts.

**With multilingual_v2 / v3 / v4:** No SSML support. Options:
- Paragraph breaks (blank lines) — creates ~0.3-0.5s natural pause
- v3/v4: audio tags such as `[long pause]`
- Post-process with ffmpeg: split audio and insert silence

**WARNING:** `...` (ellipsis) is NOT a reliable pause — it can be vocalized as a word/sound. Do not use ellipsis as a pause mechanism.

### Pronunciation Control

**Phonetic spelling (any model):** Write words as you want them pronounced:
- `Janus` → `Jan-us`
- `nginx` → `engine-x`
- Use dashes, capitals, apostrophes to guide pronunciation

**SSML phoneme tags (flash only):**
```
<phoneme alphabet="ipa" ph="ˈdʒeɪnəs">Janus</phoneme>
```

**IPA in v4:** no tags needed. Wrap the IPA in slashes and double quotes in place of the word:
```
The term "/ˌbaɪoʊˈkemɪstri/" refers to the study of chemical processes.
```

### Iterative Workflow

1. Generate → listen → identify pronunciation/pacing issues
2. Adjust: phonetic spellings, break tags, voice settings
3. Regenerate. If pauses aren't precise enough, add silence in post with ffmpeg rather than fighting the TTS engine.

## Speech to Text (Scribe)

```python
with open("voiceover.mp3", "rb") as f:
    result = client.speech_to_text.convert(file=f, model_id="scribe_v2", tag_audio_events=False)
words = [w for w in result.words if w.type == "word"]  # .text, .start, .end (seconds)
```

`scribe_v2` is current and the toolkit default. `scribe_v1` is deprecated, with removal announced for 2026-07-09 ([changelog](https://elevenlabs.io/docs/changelog/2026/6/8)), but still answers, so `--stt-model scribe_v1` (redub) and `--model scribe_v1` (align_captions) still run it, with a warning. `scribe_v1_experimental`, a 2025 preview of scribe_v1, is accepted with a warning and sent as `scribe_v2`. The toolkit uses Scribe in `redub.py` (transcribe + `--sync` word timing) and `align_captions.py`.

## Voice Cloning

### Instant Voice Clone

```python
with open("sample.mp3", "rb") as f:
    voice = client.voices.ivc.create(
        name="My Voice",
        files=[f],
        remove_background_noise=True
    )
print(f"Voice ID: {voice.voice_id}")
```

- Use `client.voices.ivc.create()` (not `client.voices.clone()`)
- Pass file handles in binary mode (`"rb"`), not paths
- Convert m4a first: `ffmpeg -i input.m4a -codec:a libmp3lame -qscale:a 2 output.mp3`
- Multiple samples (2-3 clips) improve accuracy
- Save voice ID for reuse

**Professional Voice Clone:** Requires Creator plan+, 30+ min audio. See [reference.md](reference.md).

## Sound Effects

Max 22 seconds per generation.

```python
result = client.text_to_sound_effects.convert(
    text="Thunder rumbling followed by heavy rain",
    duration_seconds=10,
    prompt_influence=0.3
)
with open("thunder.mp3", "wb") as f:
    for chunk in result:
        f.write(chunk)
```

**Prompt tips:** Be specific — "Heavy footsteps on wooden floorboards, slow and deliberate, with creaking"

## Music Generation

10 seconds to 5 minutes. Use `client.music.compose()` (not `.generate()`).

```python
result = client.music.compose(
    prompt="Upbeat indie rock, catchy guitar riff, energetic drums, travel vlog",
    music_length_ms=60000,
    force_instrumental=True
)
with open("music.mp3", "wb") as f:
    for chunk in result:
        f.write(chunk)
```

**Prompt structure:** Genre, mood, instruments, tempo, use case. Add "no vocals" or use `force_instrumental=True` for background music.

## Remotion Integration

### Complete Workflow: Script to Synchronized Scene

```
VOICEOVER-SCRIPT.md → voiceover.py → public/audio/ → Remotion composition
        ↓                  ↓               ↓                 ↓
  Scene narration    Generate MP3    Audio files     <Audio> component
  with durations     per scene       with timing     synced to scenes
```

### Step 1: Generate Per-Scene Audio

Use the toolkit's voiceover tool to generate audio for each scene:

```bash
# Generate voiceover files for each scene
uv run tools/voiceover.py --scene-dir public/audio/scenes --json

# Output:
# public/audio/scenes/
#   ├── scene-01-title.mp3
#   ├── scene-02-problem.mp3
#   ├── scene-03-solution.mp3
#   └── manifest.json  (durations for each file)
```

The `manifest.json` contains timing info:
```json
{
  "scenes": [
    { "file": "scene-01-title.mp3", "duration": 4.2 },
    { "file": "scene-02-problem.mp3", "duration": 12.8 },
    { "file": "scene-03-solution.mp3", "duration": 15.3 }
  ],
  "totalDuration": 32.3
}
```

### Step 2: Use Audio in Remotion Composition

```tsx
// src/Composition.tsx
import { Audio, staticFile, Series, useVideoConfig } from 'remotion';

// Import scene components
import { TitleSlide } from './scenes/TitleSlide';
import { ProblemSlide } from './scenes/ProblemSlide';
import { SolutionSlide } from './scenes/SolutionSlide';

// Scene durations (from manifest.json, converted to frames at 30fps)
const SCENE_DURATIONS = {
  title: Math.ceil(4.2 * 30),      // 126 frames
  problem: Math.ceil(12.8 * 30),   // 384 frames
  solution: Math.ceil(15.3 * 30),  // 459 frames
};

export const MainComposition: React.FC = () => {
  return (
    <>
      {/* Scene sequence */}
      <Series>
        <Series.Sequence durationInFrames={SCENE_DURATIONS.title}>
          <TitleSlide />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS.problem}>
          <ProblemSlide />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS.solution}>
          <SolutionSlide />
        </Series.Sequence>
      </Series>

      {/* Audio track - plays continuously across all scenes */}
      <Audio src={staticFile('audio/voiceover.mp3')} volume={1} />

      {/* Optional: Background music at lower volume */}
      <Audio src={staticFile('audio/music.mp3')} volume={0.15} />
    </>
  );
};
```

### Step 3: Per-Scene Audio (Alternative)

For more control, add audio to each scene individually:

```tsx
// src/scenes/ProblemSlide.tsx
import { Audio, staticFile, useCurrentFrame } from 'remotion';

export const ProblemSlide: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div style={{ /* slide styles */ }}>
      <h1>The Problem</h1>
      {/* Scene content */}

      {/* Audio starts when this scene starts (frame 0 of this sequence) */}
      <Audio src={staticFile('audio/scenes/scene-02-problem.mp3')} />
    </div>
  );
};
```

### Syncing Visuals to Voiceover

Calculate scene duration from audio, not the other way around:

```tsx
// src/config/timing.ts
import manifest from '../../public/audio/scenes/manifest.json';

const FPS = 30;

// Convert audio durations to frame counts
export const sceneDurations = manifest.scenes.reduce((acc, scene) => {
  const name = scene.file.replace(/^scene-\d+-/, '').replace('.mp3', '');
  acc[name] = Math.ceil(scene.duration * FPS);
  return acc;
}, {} as Record<string, number>);

// Usage in composition:
// <Series.Sequence durationInFrames={sceneDurations.title}>
```

### Audio Timing Patterns

```tsx
import { Audio, Sequence, interpolate, useCurrentFrame } from 'remotion';

// Fade in audio
export const FadeInAudio: React.FC<{ src: string; fadeFrames?: number }> = ({
  src,
  fadeFrames = 30
}) => {
  const frame = useCurrentFrame();
  const volume = interpolate(frame, [0, fadeFrames], [0, 1], {
    extrapolateRight: 'clamp',
  });
  return <Audio src={src} volume={volume} />;
};

// Delayed audio start
export const DelayedAudio: React.FC<{ src: string; delayFrames: number }> = ({
  src,
  delayFrames
}) => (
  <Sequence from={delayFrames}>
    <Audio src={src} />
  </Sequence>
);

// Usage:
// <FadeInAudio src={staticFile('audio/music.mp3')} fadeFrames={60} />
// <DelayedAudio src={staticFile('audio/sfx/whoosh.mp3')} delayFrames={45} />
```

### Voiceover + Demo Video Sync

When a scene has both voiceover and demo video:

```tsx
import { Audio, OffthreadVideo, staticFile, useVideoConfig } from 'remotion';

export const DemoScene: React.FC = () => {
  const { durationInFrames, fps } = useVideoConfig();

  // Calculate playback rate to fit demo into voiceover duration
  const demoDuration = 45; // seconds (original demo length)
  const sceneDuration = durationInFrames / fps; // seconds (from voiceover)
  const playbackRate = demoDuration / sceneDuration;

  return (
    <>
      <OffthreadVideo
        src={staticFile('demos/feature-demo.mp4')}
        playbackRate={playbackRate}
      />
      <Audio src={staticFile('audio/scenes/scene-04-demo.mp3')} />
    </>
  );
};
```

### Error Handling

```tsx
import { Audio, staticFile, delayRender, continueRender } from 'remotion';
import { useEffect, useState } from 'react';

export const SafeAudio: React.FC<{ src: string }> = ({ src }) => {
  const [handle] = useState(() => delayRender());
  const [audioReady, setAudioReady] = useState(false);

  useEffect(() => {
    const audio = new window.Audio(src);
    audio.oncanplaythrough = () => {
      setAudioReady(true);
      continueRender(handle);
    };
    audio.onerror = () => {
      console.error(`Failed to load audio: ${src}`);
      continueRender(handle); // Continue without audio rather than hang
    };
  }, [src, handle]);

  if (!audioReady) return null;
  return <Audio src={src} />;
};
```

### Toolkit Command: /generate-voiceover

The `/generate-voiceover` command handles the full workflow:

```
/generate-voiceover

1. Reads VOICEOVER-SCRIPT.md
2. Extracts narration for each scene
3. Generates audio via ElevenLabs API
4. Saves to public/audio/scenes/
5. Creates manifest.json with durations
6. Updates project.json with timing info
```

## Popular Voices

- George: `JBFqnCBsd6RMkjVDRZzb` (warm narrator)
- Rachel: `21m00Tcm4TlvDq8ikWAM` (clear female)
- Adam: `pNInz6obpgDQGcFmaJgB` (professional male)

List all: `client.voices.get_all()`

For full API docs, see [reference.md](reference.md).
