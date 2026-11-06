---
description: Redub video with a different voice
---

# Redub Video

Replace the voice in an existing video using ElevenLabs transcription + TTS.

This is a **utility command** - it works on any video file without requiring a project structure.

## Pipeline

```
Input Video → Extract Audio → Transcribe → TTS (new voice) → Replace Audio → Output Video
```

## Entry Point

### Step 1: Get Input Video

Ask the user for the input video:

```
/redub - Replace voice in a video

Enter the path to the video you want to redub:
```

If user provides a path, verify it exists. If not found, list recent MP4 files:
```bash
find . -name "*.mp4" -type f -mtime -7 | head -10
```

### Step 2: Choose Target Voice

Help the user choose a voice. Options:

**Option A - Use default voice:**
Check `ELEVENLABS_VOICE_ID` env var or `toolkit-registry.json` config.

**Option B - List available voices:**
```bash
# User can find voices at: https://elevenlabs.io/app/voice-library
# Or use the API to list voices
```

**Option C - User provides voice ID:**
Ask for the ElevenLabs voice ID directly.

Present as a question:
```
Which voice should narrate the redubbed video?

1. Use default voice (from .env or registry)
2. Enter a voice ID
3. Help me find a voice (opens ElevenLabs voice library)
```

### Step 3: Transcript Handling

Ask how to handle the transcript:

```
How should we handle the transcript?

1. Auto-transcribe and generate (no review)
2. Auto-transcribe, let me review before TTS (recommended for accuracy)
3. I have my own transcript file
```

If option 2: set `--save-transcript transcript.txt` and pause for review.
If option 3: ask for transcript file path.

### Step 4: Output Location

Suggest default output path:
```
Output: {input_stem}_redubbed.mp4

Accept default or enter custom path:
```

### Step 5: Execute

Run the redub tool:

```bash
source .venv/bin/activate && uv run tools/redub.py \
  --input "INPUT_PATH" \
  --voice-id "VOICE_ID" \
  --output "OUTPUT_PATH" \
  --json
```

For transcript review workflow:
```bash
# Step 1: Transcribe only
source .venv/bin/activate && uv run tools/redub.py \
  --input "INPUT_PATH" \
  --voice-id "VOICE_ID" \
  --output "OUTPUT_PATH" \
  --save-transcript transcript.txt \
  --dry-run

# Show transcript to user, let them edit
# Step 2: After approval, run with edited transcript
source .venv/bin/activate && uv run tools/redub.py \
  --input "INPUT_PATH" \
  --voice-id "VOICE_ID" \
  --output "OUTPUT_PATH" \
  --transcript transcript.txt \
  --json
```

### Step 6: Report Results

Parse the JSON output and report:

```
Redub complete!

Input:  original.mp4 (45.2s)
Output: original_redubbed.mp4 (47.1s)
Voice:  {voice_id}

Duration change: +1.9s
(The new voice speaks slightly slower than the original)

Keep intermediate files? [y/N]
```

If duration differs significantly (>5s), suggest:
- Adjusting `--speed` parameter
- Editing the transcript to shorten/lengthen

---

## Quick Mode

For experienced users, support direct invocation:

```
/redub my_video.mp4 --voice-id ABC123
```

Parse arguments and skip interactive prompts.

---

## Tool Reference

| Option | Description |
|--------|-------------|
| `--input, -i` | Input video file |
| `--output, -o` | Output video file |
| `--voice-id, -v` | Target voice ID |
| `--transcript, -t` | Use existing transcript (skip STT) |
| `--save-transcript` | Save transcription for review |
| `--language, -l` | Force language (auto-detects by default) |
| `--speed` | Adjust TTS speed (default: 1.0) |
| `--keep-temp` | Keep extracted/generated audio files |
| `--dry-run` | Preview what would happen |

---

## Use Cases

- **Voice replacement**: Replace your voice with a professional narrator
- **Anonymization**: Replace identifiable voices in demos
- **Localization prep**: Get transcript for translation (then TTS in target language)
- **Voice consistency**: Re-record old videos with your current cloned voice
- **Accessibility**: Generate clearer narration for videos with poor audio

---

## Limitations

- **Timing**: New TTS won't match original timing exactly. Use `--speed` to adjust.
- **Non-speech audio**: Background music, sound effects are lost. Extract those separately if needed.
- **Multiple speakers**: Currently treats all speech as single speaker. Diarization possible but not implemented.

---

## Error Handling

| Error | Solution |
|-------|----------|
| `ELEVENLABS_API_KEY not found` | Add to `.env` file |
| `No voice ID provided` | Use `--voice-id` or set `ELEVENLABS_VOICE_ID` in `.env` |
| `Failed to extract audio` | Check FFmpeg is installed |
| `Failed to transcribe` | Check API key, file size (<3GB) |

---

## Evolution

This command evolves through use. If something's awkward or missing:

**Local improvements:**
1. Say "improve this" → Claude captures in `_internal/BACKLOG.md`
2. Edit `.claude/commands/redub.md` → Update `_internal/CHANGELOG.md`

**Remote contributions:**
- Issues: `github.com/digitalsamba/claude-code-video-toolkit/issues`
- PRs welcome for multi-speaker support, timing sync, etc.
