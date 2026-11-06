---
name: jaystudio
description: Jaystudio — studio video production toolkit. Use for any video work: planning a script/storyboard, building motion graphics or programmatic videos in Remotion, auto-editing/cutting/captioning/transcoding footage (mcp-video, VibeFrame, ffmpeg, moviepy), AI voiceover/music/image/clip generation (video-toolkit, Pixelle/ComfyUI), thumbnails, demo recordings and final export.
---

# Jaystudio

Jaystudio is a single entry point that bundles five video stacks. Pick the module that fits the task,
then **read that module's SKILL.md before writing code** — the files below are the source of truth.

| Need | Module | Where |
|---|---|---|
| Programmatic video / motion graphics in React | Remotion skills (official) | `remotion/` |
| Edit, trim, merge, caption, resize, transcode existing footage | `mcp-video` MCP server | tools `mcp__mcp-video__*` |
| AI-native editing, timeline, scene/script → video | `vibeframe` MCP server | tools `mcp__vibeframe__*` |
| Brief → finished explainer MP4 (voiceover, visuals, captions, QC) | Claude Code Video Toolkit | `video-toolkit/` + tools `mcp__video-toolkit__*` |
| ComfyUI workflows as tools (image/video/audio gen, TISV) | Pixelle-MCP | tools `mcp__pixelle__*` (server must be running) |

## Module index

### `remotion/` — official Remotion agent skills (remotion-dev/skills)
Start at `remotion/remotion-best-practices/SKILL.md` (router), then:
- `remotion-create` — new Remotion project/video
- `remotion-markup` — content, animation, effects, transitions, audio, fonts, timing
- `remotion-captions` — transcribe, display and animate captions
- `remotion-multimedia` — Mediabunny (decode/encode/inspect media)
- `remotion-maps` — map animations
- `remotion-interactivity` — markup for interactive players
- `remotion-studio` — preview; `remotion-render` — export
- `remotion-saas` — build an app on Remotion; `remotion-upgrade`; `remotion-docs`; `remotion-license`

### `video-toolkit/` — digitalsamba/claude-code-video-toolkit
- `video-toolkit/SKILL.md` — quick path: spec → `video_job.py submit` → poll → result
- `video-toolkit/skills/<name>/SKILL.md` — acestep (music), elevenlabs (voice/SFX), ffmpeg, ideogram4,
  ltx2 (AI clips), moviepy, playwright-recording, qwen-edit, remotion (toolkit conventions),
  runpod (cloud GPU), synthetic-ui-demo, video-design
- `video-toolkit/commands/*.md` — workflows: video, brand, design, generate-voiceover, voice-clone,
  redub, record-demo, scene-review, thumbnail, template, publish, setup, versions
- Toolkit code lives at `$VIDEO_TOOLKIT_ROOT` (default `~/claude-code-video-toolkit`); run its tools
  from that root: `uv run tools/verify_setup.py --json`

## Default Jaystudio workflow
1. **Brief** — goal, audience, platform/format (16:9, 9:16, 1:1), length, tone, brand assets.
2. **Script & storyboard** — scenes with narration (~2.4 words/sec) + one visual per scene.
3. **Build** — Remotion for designed motion graphics; video-toolkit for brief→MP4; Pixelle/ComfyUI or
   LTX for generated clips/images; VibeFrame for AI timeline editing.
4. **Edit & finish** — mcp-video / ffmpeg: trim, concat, audio mix, captions, loudness, resize per platform.
5. **QC & package** — check duration, sync, captions, safe areas; export MP4 + thumbnail.

## Setup / health
- One-shot install: `bash .claude/skills/jaystudio/setup.sh`
- Check: `mcp-video doctor`, `claude mcp list`, `pixelle status`
- Pixelle needs a ComfyUI URL or RunningHub key + an LLM key: run `pixelle init` (or `pixelle`) once,
  then `pixelle start` — MCP endpoint `http://localhost:9004/pixelle/mcp`.
- Optional keys for the toolkit (ElevenLabs, RunPod, etc.) go in `~/claude-code-video-toolkit/.env`.
