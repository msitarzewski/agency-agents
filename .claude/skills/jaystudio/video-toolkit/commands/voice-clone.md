---
description: Record, test, and save a cloned voice to a brand profile
---

# Voice Clone

Guided workflow to set up Qwen3-TTS voice cloning for a brand. Records or imports reference audio, tests the clone, and saves the profile so `--brand` loads it automatically.

## Step 1: Check Dependencies

Verify the environment is ready:

```
1. Check .env for RUNPOD_API_KEY
   - If missing: "Add `RUNPOD_API_KEY=your_key` to `.env`"
2. Check .env for RUNPOD_QWEN3_TTS_ENDPOINT_ID
   - If missing and API key exists: offer to run `uv run tools/qwen3_tts.py --setup`
   - If API key also missing: guide user to add it first
3. Only proceed once both are confirmed
```

Use Grep to check `.env` for both keys. If the endpoint is missing but the API key exists, offer to run setup automatically.

## Step 2: Choose Brand

Scan for available brands:

```
1. Glob brands/*/brand.json
2. For each brand, check if voice.json exists and has a qwen3.clone section
3. Present list:

   Available brands:

     1. default — no clone profile
     2. digital-samba — clone configured (assets/voice-reference.m4a)

   Which brand should this voice clone be saved to?
```

If the selected brand already has a clone profile, show the existing config and ask:
- **Test existing clone** — generate a sample to hear it
- **Replace** — record/import new reference audio
- **Cancel** — exit

## Step 3: Record or Provide Reference Audio

Present a reference script for the user to read aloud. The script should be ~15-20 seconds and include varied intonation:

```
Suggested script to read aloud (~15 seconds):

  "Welcome to this video walkthrough. Today we'll explore some exciting
   new features — including improved performance, better accessibility,
   and a redesigned dashboard. There's a lot to cover, so let's take it
   step by step and get started!"

Options:
  1. I'll record this script (provide the file path when ready)
  2. I have my own audio sample
  3. Use an existing file (enter path)
```

**Read it at the pace you want the clone to narrate at.** The clone inherits
its speaking rate from the reference, and temperature/regeneration cannot
correct pace afterwards — a short, snappy reference reliably produces rushed
(170-210 wpm) narration on every take.

Once the user provides the audio file:
1. Verify the file exists and is a supported format (wav, mp3, m4a, flac, ogg)
2. **Validate the reference** before accepting it:
   ```bash
   ffprobe -v error -show_entries format=duration -of csv=p=0 REFERENCE_FILE
   ```
   - Duration **< 8s**: warn strongly — too little prosody to anchor pace or
     tone; the clone will sound rushed and flat. Recommend re-recording.
   - Duration **8-12s**: usable, but suggest a longer take if convenient.
   - Duration **12-25s**: ideal.
   - Also sanity-check content: fewer than ~25 words of varied, full-sentence
     speech (e.g. a repeated short phrase like "Thank you. Thank you.") gives
     the model no narration pacing to copy — warn and offer to proceed anyway.
3. Copy it to `brands/{name}/assets/voice-reference.{ext}`
4. Confirm the copy

## Step 4: Transcript

Determine the transcript for the reference audio:

```
What was said in the recording?

  1. I read the suggested script above (use that as transcript)
  2. I'll type the exact transcript
```

If option 1: use the suggested script text.
If option 2: ask the user to type or paste the exact words spoken.

The transcript must match what was actually said — this is critical for clone quality.

## Step 5: Test the Clone

Generate a test clip using the reference audio:

```bash
uv run tools/qwen3_tts.py \
  --text "This is a test of the cloned voice. It should sound natural and similar to the original recording." \
  --ref-audio brands/{name}/assets/voice-reference.{ext} \
  --ref-text "TRANSCRIPT_HERE" \
  --output /tmp/voice-clone-test.mp3
```

After generation:
```
Clone test generated: /tmp/voice-clone-test.mp3

Listen to the result and let me know:
  1. Sounds good — save this profile
  2. Not quite right — re-record with different audio
  3. Try with a different test phrase
  4. Cancel
```

If the user wants to retry, go back to Step 3.

## Step 6: Save to Brand

Before saving, ask about a default voice tone for this brand:

```
Would you like to set a default tone for this brand's Qwen3-TTS voice?

  1. Neutral (no instruction)
  2. Warm — friendly, conversational
  3. Professional — clear, measured
  4. Tutorial — patient, step-by-step
  5. Custom instruction (type your own)
  6. Skip — no default tone
```

If a tone is selected, save it in the `tone` field. If a custom instruction is provided, save it in the `instruct` field instead.

Update `brands/{name}/voice.json` to add/update the `qwen3` section (including clone and tone):

```json
{
  "voiceId": "...",
  "settings": { ... },
  "qwen3": {
    "speaker": "Ryan",
    "language": "Auto",
    "tone": "warm",
    "instruct": "",
    "clone": {
      "refAudio": "assets/voice-reference.{ext}",
      "refText": "Exact transcript of the reference audio."
    }
  }
}
```

Important:
- `refAudio` path is **relative to the brand directory**
- `tone` is a named preset (e.g., "warm", "professional"). `instruct` is raw text override. `instruct` takes precedence over `tone`.
- Preserve all existing fields in voice.json (ElevenLabs config, etc.)
- If no `qwen3` section exists yet, create one with sensible defaults
- If `qwen3` exists but no `clone`, add just the `clone` sub-object

## Step 7: Show Usage

```
Voice clone saved to: brands/{name}/voice.json

Usage:

  # Per-scene voiceover with cloned voice
  uv run tools/voiceover.py --provider qwen3 --brand {name} --scene-dir public/audio/scenes --json

  # Single file
  uv run tools/voiceover.py --provider qwen3 --brand {name} --script script.txt --output out.mp3

  # In /generate-voiceover, select Qwen3-TTS — the clone profile will be detected automatically.

The clone profile is stored in brands/{name}/voice.json and will be loaded
automatically whenever you use --brand {name} with --provider qwen3.
```

---

## Tool Locations

- Qwen3-TTS tool: `tools/qwen3_tts.py`
- Voiceover tool: `tools/voiceover.py`
- Brand voice config: `brands/{name}/voice.json`
- Reference audio: `brands/{name}/assets/voice-reference.{ext}`

## Voice Clone Tips

Share these with the user:

- **Recording quality matters** — use a quiet room, consistent mic distance
- **12-25 seconds** of reference audio is ideal (too short = poor quality + rushed pace, too long = diminishing returns)
- **The clone copies your pace** — read the reference at narration speed; rushed or punchy references produce rushed clones, and no generation setting fixes it afterwards (use `--max-wpm 165` on voiceover.py/qwen3_tts.py as a deterministic safety net)
- **Varied intonation** helps — include questions, emphasis, and natural pauses; avoid repeating one short phrase
- **Transcript accuracy** is critical — must match the audio exactly
- **Supported formats:** wav, mp3, m4a, flac, ogg (wav or m4a preferred)

---

## Integration

This command is referenced by:
- `/brand` — Step 5 offers voice clone setup via `/voice-clone`
- `/generate-voiceover` — detects brand clone profiles when Qwen3-TTS is selected
