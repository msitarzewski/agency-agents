---
description: First-time toolkit setup - cloud GPU, file transfer, voice, and prerequisites
---

# Setup

Interactive setup wizard for new users. Checks prerequisites, guides cloud GPU and storage configuration, deploys AI tools, and verifies everything works. Idempotent — safe to run again to add features or verify configuration.

## Key Principles

- **Progressive disclosure** — one phase at a time, explain before asking
- **Cost transparency** — always state what's free and what costs money before any action
- **Idempotent** — check what's already configured, skip completed steps
- **Test after each step** — don't just save keys, verify they work
- **Skippable** — every phase can be skipped, user can return later
- **Claude Code native** — use bash tools to check, configure, and verify. This IS the setup wizard.

## Entry Point

On invocation, assess current state and adapt:

### Step 1: Detect Current State

```
1. Check .env exists — if not, create from .env.example
2. Read current .env values (which keys are set vs placeholder)
3. Check prerequisites: node --version, uv --version, ffmpeg -version
4. Check Python deps: uv run python -c "import dotenv; import requests"
5. Check Modal CLI: uv run modal --version (if installed)
6. Check for existing Modal apps: uv run modal app list (if authenticated)
7. Summarize what's ready vs what needs setup
```

### Step 2: Present Current State

Show a clear status overview before asking anything:

```
Toolkit Setup

Prerequisites:
  [check] Node.js 24.x
  [check] Python 3.12
  [check] FFmpeg 7.1
  [check] Python deps installed (uv)

Cloud GPU:      Not configured
File transfer:  Not configured (using free fallback services)
Voice:          Not configured
ElevenLabs:     Not configured (optional, paid)

Let's get you set up! We'll go through each feature one at a time.
You can skip any step and come back later with /setup.
```

**If everything is already configured**, show status and offer to verify/test:

```
Toolkit Setup — All Configured

Cloud GPU:      Modal (7 tools deployed)
File transfer:  Cloudflare R2 (bucket: video-toolkit)
Voice:          Qwen3-TTS (speaker: Ryan)
ElevenLabs:     Configured

Everything looks good! Want me to run a quick verification test?
```

---

## Phase 1: Prerequisites

Check and report. Don't install anything automatically — just tell the user what's needed and how to get it.

### Required

- **Node.js 22+ (24 LTS recommended)**: `node --version`. If missing: "Install from https://nodejs.org/ — needed to render videos". If it is 18 or 20, it still works, but both are end of life: suggest `nvm install 24 && nvm alias default 24`
- **Claude Code**: Already running if they're seeing this command

### Recommended

- **uv**: `uv --version`. If missing: "Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"` (Windows) — manages Python and all toolkit dependencies; needed for AI voiceover, image editing, and all cloud GPU tools"
- **Python deps**: `uv run python -c "import dotenv; import requests"`. If missing: run `uv sync` from the toolkit root (uv installs a compatible Python automatically if needed)
- **FFmpeg**: `ffmpeg -version`. If missing: "Install with `brew install ffmpeg` (macOS) or see https://ffmpeg.org/ — needed for media conversion"

### Windows only

**Export `PYTHONIOENCODING=utf-8` before running any deploy command in this wizard.** On
Windows, a piped/captured stdout defaults to the `cp1252` codec. Modal's deploy progress
output contains box-drawing characters it cannot encode, so `modal deploy` aborts partway
through the image build with:

```
'charmap' codec can't encode characters in position 3-42: character maps to <undefined>
```

The build itself is fine — only the *printing* fails, which makes this look like a broken
deploy or a network problem rather than an encoding one. Every deploy in Phase 4 fails
identically without it.

Set it for the shell you run the deploys in:

```bash
export PYTHONIOENCODING=utf-8   # Git Bash
$env:PYTHONIOENCODING = 'utf-8' # PowerShell
```

Offer to make it permanent so the user does not hit this again outside this wizard:

```powershell
[Environment]::SetEnvironmentVariable('PYTHONIOENCODING','utf-8','User')
```

See `docs/modal-setup.md` for the rest of the Windows prerequisites (notably the
Microsoft Store `python3` stub).

### Output

```
Prerequisites: 4/4 ready

Moving on to cloud GPU setup...
```

If anything critical is missing, explain what features require it and ask if user wants to continue or fix first.

---

## Phase 2: Cloud GPU Provider

This is the biggest unlock. Frame it properly.

### Explanation (deliver conversationally, not as a wall of text)

Explain what cloud GPU enables:
- AI voiceovers (Qwen3-TTS) — free, self-hosted text-to-speech
- AI image generation (FLUX.2) — title backgrounds, thumbnails
- AI image editing (Qwen-Edit) — transform photos, add effects
- AI upscaling (RealESRGAN) — enhance image quality
- AI music generation (ACE-Step) — background music, jingles
- Talking heads (SoulX-FlashHead, SadTalker) — animated presenters from a photo
- Watermark removal (ProPainter) — clean up stock footage

Then present the choice:

### Option A: Modal (Recommended)

Frame the pitch:
- **$30/month free compute** on the Starter plan — just requires adding a payment method
- All 7 toolkit tools typically cost $0.50-2.00/month with normal use
- Faster cold starts than RunPod
- Scale to zero — no charges when idle
- Simple deployment: `uv run tools/modal_setup.py <app>` (deploys and writes `.env`)

Setup flow:
```
1. uv sync --extra modal
2. uv run modal setup
   → Opens browser for authentication
   → Creates ~/.modal.toml with credentials
3. Verify: uv run modal app list
```

### Option B: RunPod

Frame honestly:
- Pay-as-you-go, typically $0.44/hr for GPU time
- Each job usually costs $0.01-0.50 depending on the tool
- More GPU variety available
- `--setup` flag automates endpoint creation
- **Availability can be spotty** — GPUs may not be available in some regions

Setup flow:
```
1. Create account at https://runpod.io/
2. Get API key from https://runpod.io/console/user/settings
3. Add to .env: RUNPOD_API_KEY=your_key_here
4. Each tool has --setup to create its endpoint automatically
```

### Option C: Both

Explain dual-provider benefits:
- Switch between providers with `--cloud modal` or `--cloud runpod`
- If one provider is down, use the other
- Modal for daily use (free tier), RunPod as fallback

### Option D: Skip

"No problem — you can still create and render videos with just Node.js. Run /setup anytime to add cloud features later."

---

## Phase 3: Cloudflare R2 (File Transfer)

**Only show this phase if user chose a cloud GPU provider.**

### Explanation

"When you run a cloud GPU tool (like generating a voiceover or editing an image), the tool needs to send your file to the remote GPU and get the result back. Cloudflare R2 is the bridge.

**R2 is free** — 10GB storage, 10 million operations/month, and zero egress fees. That's more than enough for this toolkit. Without R2, tools fall back to free file hosting services (litterbox, 0x0.st) which are slower and less reliable."

### Setup Flow

Guide the user step by step. They'll need to do some of this in their browser:

```
1. Go to https://dash.cloudflare.com/
   → Create a free account if you don't have one

2. In the sidebar, click "R2 Object Storage"
   → Click "Create bucket"
   → Name it: video-toolkit (or whatever you prefer)
   → Choose automatic region
   → Click "Create bucket"

3. Go to R2 > Overview > "Manage R2 API Tokens"
   → Click "Create API Token"
   → Name: "video-toolkit"
   → Permissions: "Object Read & Write"
   → Scope: Apply to specific bucket → select your bucket
   → Click "Create API Token"
   → COPY the Access Key ID and Secret Access Key (shown only once!)

4. Your Account ID is in the URL: dash.cloudflare.com/{account_id}/r2
   Or find it in the R2 overview sidebar
```

After user provides the values, write them to .env:
```
R2_ACCOUNT_ID=xxx
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=video-toolkit
```

### Verify

Test R2 connectivity:
```bash
uv run python -c "
import sys; sys.path.insert(0, 'tools')
from file_transfer import upload_to_r2, delete_from_r2
import tempfile, os
# Create tiny test file
tmp = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
tmp.write(b'R2 connectivity test')
tmp.close()
url, key = upload_to_r2(tmp.name, 'setup-test')
os.unlink(tmp.name)
if url:
    print(f'R2 working! Test upload succeeded.')
    delete_from_r2(key)  # Clean up
else:
    print('R2 upload failed — check credentials')
"
```

---

## Phase 4: Deploy Cloud GPU Tools

**Only show this phase if user chose a cloud GPU provider in Phase 2.**

### Tool Selection

Present all 7 tools with descriptions and let user choose:

```
Which AI tools would you like to set up?

  1. [recommended] Speech (Qwen3-TTS)
     Free AI voiceovers — 9 speakers, voice cloning, tone presets
     This is the most-used tool in the toolkit.

  2. [recommended] Images (FLUX.2 klein)
     Generate title backgrounds, scene illustrations, thumbnails
     Fast: ~3s per image on warm GPU
     Default klein-4B (Apache-2.0); klein-9B is a non-commercial opt-in

  3. Image Editing (Qwen-Image-Edit-2511)
     Transform photos — add/remove objects, change style, backgrounds
     Note: Large model, ~2 min cold start
     Qwen-Image-2.1 is a non-commercial opt-in (up to 10 input images)

  4. Upscaling (RealESRGAN)
     Enhance image quality 2x or 4x with AI
     Fast: ~5s per image

  5. Music (ACE-Step 1.5)
     Generate background music, jingles, vocals
     8 scene presets: corporate, ambient, dramatic, tension, cta...

  6. Talking Heads (SoulX-FlashHead + SadTalker)
     Animate a portrait photo with lip-sync from audio
     Great for narrator Picture-in-Picture
     SoulX is the default (Modal only, one-off 15GB weights download);
     SadTalker is the cheap draft option

  7. Watermark Removal (ProPainter)
     Remove watermarks from video using AI inpainting

  a. All of the above (recommended)
  s. Skip for now
```

Recommend "all" — with Modal's free tier, there's no cost to having them deployed (they scale to zero).

### Modal Deployment Flow

Deploy the selected apps with `tools/modal_setup.py`. It deploys one at a time (Modal
rate-limits parallel `AppCreate`), runs SoulX's `populate_weights` first, reads each
endpoint URL from Modal's API, and writes it to `.env`. Don't parse URLs out of the deploy
log yourself, because Modal wraps and truncates them.

```bash
# Windows: required, or the deploys die with a 'charmap' codec error mid-build.
# Harmless everywhere else.
export PYTHONIOENCODING=utf-8

uv run tools/modal_setup.py --all                       # "all of the above"
uv run tools/modal_setup.py qwen3_tts flux2 soulx       # or just the chosen ones
```

Map menu choices to app names: `qwen3_tts`, `flux2`, `image_edit`, `upscale`,
`music_gen`, `sadtalker`, `soulx`, `dewatermark` (ProPainter). `--all` deploys these
eight. `ltx2` is never included: offer it separately, and only after the user confirms
the Hugging Face secret and their Gemma 3 access (see `docs/modal-setup.md`).

Deploys stream their logs and can take 5-15 minutes each on a first build, so run the
command in the background and report each app's `OK`/`!!` line as it lands. A failed app
prints a hint (payment method, rate limit, Hugging Face access); fix it and re-run with
just that app's name.

If the user already deployed some apps by hand, `uv run tools/modal_setup.py --sync-env`
writes the live URLs to `.env` without redeploying anything. `--list` shows what's
deployed and whether `.env` agrees.

### RunPod Deployment Flow

For each selected tool, run the `--setup` command:

```bash
uv run tools/qwen3_tts.py --setup
uv run tools/flux2.py --setup
uv run tools/image_edit.py --setup
uv run tools/upscale.py --setup
uv run tools/music_gen.py --setup
uv run tools/sadtalker.py --setup
uv run tools/dewatermark.py --setup
```

Each `--setup` command creates a RunPod template + endpoint and saves the endpoint ID to .env automatically.

### Smoke Test

After deployment, run a quick test for at least one tool to verify the pipeline works:

**If Qwen3-TTS was deployed (most common):**
```bash
uv run tools/qwen3_tts.py --text "Setup complete! Your video toolkit is ready." \
  --speaker Ryan --tone warm --output /tmp/setup-test.mp3 \
  --cloud modal
```

Check that it produces an audio file. If it does, the full pipeline (upload → cloud GPU → download) is working.

**If FLUX.2 was deployed:**
```bash
uv run tools/flux2.py --prompt "A minimal geometric logo on dark background" \
  --output /tmp/setup-test.png --cloud modal
```

---

## Phase 5: Voice Setup

### Explanation

"For voiceovers in your videos, you have two options:

**Qwen3-TTS (recommended, free)**
Self-hosted on your cloud GPU. 9 built-in speakers, tone presets (warm, professional, excited...), and voice cloning. This is what most toolkit users use.

**ElevenLabs (optional, paid)**
Premium cloud TTS with a large voice library. Pay-per-character. Better for some specific voice styles, but Qwen3-TTS is comparable quality for most use cases."

### Qwen3-TTS Setup

If Qwen3-TTS was deployed in Phase 4, it's already ready. Just confirm the default speaker:

```
Qwen3-TTS is ready! Available speakers:
  Ryan, Aiden, Vivian, Luna, Aurora, Aria, Nova, Stella, Orion

Default speaker: Ryan (warm male voice)

You can change the speaker per-video or set a default in your brand's voice.json.
To preview voices: uv run tools/qwen3_tts.py --list-voices
```

### ElevenLabs Setup (Optional)

```
1. Sign up at https://elevenlabs.io/
2. Go to Profile → API Keys
3. Copy your API key
```

After user provides the key, write to .env:
```
ELEVENLABS_API_KEY=xxx
```

Optionally set a default voice ID:
```
ELEVENLABS_VOICE_ID=xxx
```

Mention: "You can also use /voice-clone later to clone your own voice for a personal touch."

---

## Phase 6: Verify & Summary

### Run Final Checks

```python
# Check .env has the expected values
1. Read .env
2. For each configured service, verify connectivity:
   - R2: test upload/download
   - Modal: modal app list (check apps are deployed)
   - RunPod: check API key works
   - ElevenLabs: test API key
3. Report results
```

### Present Summary

```
Setup Complete!

Prerequisites:
  [check] Node.js 24.x
  [check] Python 3.12
  [check] FFmpeg 7.1
  [check] Python deps (uv)

Cloud GPU: Modal
  [check] Speech (Qwen3-TTS) — deployed
  [check] Images (FLUX.2) — deployed
  [check] Image Editing (Qwen-Edit) — deployed
  [check] Upscaling (RealESRGAN) — deployed
  [check] Music (ACE-Step) — deployed
  [check] Talking Heads (SadTalker) — deployed
  [check] Watermark Removal (ProPainter) — deployed

File Transfer: Cloudflare R2
  [check] Bucket: video-toolkit
  [check] Upload/download verified

Voice: Qwen3-TTS (Ryan)
  [check] Test generation successful

ElevenLabs: Not configured (optional)

Cost summary:
  - Modal: $30/mo free compute (you'll use ~$1-2/mo typical)
  - R2: Free (10GB storage, zero egress)
  - Qwen3-TTS: Free (runs on Modal compute)
  - ElevenLabs: Not configured

You're ready! Run /video to create your first video.
```

---

## Re-run Behavior

When `/setup` is run again on an already-configured toolkit:

1. Show current state (Phase 6 summary style)
2. Offer options:
   - "Verify everything works" → run smoke tests
   - "Add a new tool" → jump to Phase 4 tool selection
   - "Change cloud provider" → jump to Phase 2
   - "Set up ElevenLabs" → jump to Phase 5
   - "Everything looks good" → exit

---

## Writing to .env

When adding or updating values in `.env`:

1. Read the current .env file
2. For each new value:
   - If the key exists (even commented out), uncomment and update it
   - If the key doesn't exist, append it in the appropriate section
3. Never remove existing values
4. Preserve comments and formatting
5. Show the user what was written

Example approach:
```python
# Read .env, update/add the key, write back
lines = Path('.env').read_text().splitlines()
# ... find and update or append
```

---

## Error Handling

- If `modal deploy` fails: show the error, suggest checking `uv run modal app logs`, offer to retry
- If R2 test fails: re-check credentials, common issue is wrong bucket name or region
- If RunPod setup fails: check API key, check account has billing enabled
- If any step fails, don't block subsequent steps — mark as failed and continue
- Always show what succeeded even if something failed

---

## Verification Script

Use `tools/verify_setup.py` throughout and at the end of setup:

```bash
# Quick check (no cloud calls) — use at start to detect current state
uv run tools/verify_setup.py

# With smoke tests (makes cloud GPU calls, ~$0.01) — use at end to verify
uv run tools/verify_setup.py --test

# Machine-readable — use to programmatically check what's configured
uv run tools/verify_setup.py --json
```

Run `verify_setup.py --json` at the start of `/setup` to detect current state and skip already-configured phases. Run it with `--test` at the end for the Phase 6 verification.

## Integration with Other Commands

- `/video` should check for cloud GPU configuration and mention `/setup` if not configured
- `/generate-voiceover` should suggest `/setup` if no TTS provider is configured
- `/versions` could include a setup status check

---

## Evolution

### Local improvements (no upstream contribution needed)
- Add `--quick` flag to skip explanations and just deploy everything with defaults
- Add `--verify` flag to only run smoke tests on existing configuration
- Add `--reset` flag to clear all configuration and start fresh

### Upstream contribution candidates
- The command pattern itself could be useful for other Claude Code toolkits
- R2 setup flow is generic enough to extract as a reusable guide
