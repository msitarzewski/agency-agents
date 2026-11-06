---
name: ffmpeg
description: Video and audio processing with FFmpeg. Use for format conversion, resizing, compression, audio extraction, and preparing assets for Remotion. Triggers include converting GIF to MP4, resizing video, extracting audio, compressing files, or any media transformation task.
---

# FFmpeg for Video Production

FFmpeg is the essential tool for video/audio processing. This skill covers common operations for Remotion video projects.

## Quick Reference

### GIF to MP4 (Remotion-compatible)

```bash
ffmpeg -i input.gif -movflags faststart -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" output.mp4
```

**Why these flags:**
- `-movflags faststart` - Moves metadata to start for web streaming
- `-pix_fmt yuv420p` - Ensures compatibility with most players
- `scale=trunc(...)` - Forces even dimensions (required by most codecs)

### Resize Video

```bash
# To 1920x1080 (maintain aspect ratio, add black bars)
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" output.mp4

# To 1920x1080 (crop to fill)
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" output.mp4

# Scale to width, auto height
ffmpeg -i input.mp4 -vf "scale=1280:-2" output.mp4
```

### Compress Video

```bash
# Good quality, smaller file (CRF 23 is default, lower = better quality)
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k output.mp4

# Aggressive compression for web preview
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -preset fast -c:a aac -b:a 96k output.mp4

# Target file size (e.g., ~10MB for 60s video = ~1.3Mbps)
ffmpeg -i input.mp4 -c:v libx264 -b:v 1300k -c:a aac -b:a 128k output.mp4
```

### Extract Audio

```bash
# Extract to MP3
ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 2 output.mp3

# Extract to AAC
ffmpeg -i input.mp4 -vn -acodec aac -b:a 192k output.m4a

# Extract to WAV (uncompressed)
ffmpeg -i input.mp4 -vn output.wav
```

### Convert Audio Formats

```bash
# M4A to MP3 (for ElevenLabs voice samples)
ffmpeg -i input.m4a -codec:a libmp3lame -qscale:a 2 output.mp3

# WAV to MP3
ffmpeg -i input.wav -codec:a libmp3lame -b:a 192k output.mp3

# Adjust volume
ffmpeg -i input.mp3 -filter:a "volume=1.5" output.mp3
```

### Trim/Cut Video

```bash
# Cut from timestamp to duration (recommended - reliable)
ffmpeg -i input.mp4 -ss 00:00:30 -t 00:00:15 -c:v libx264 -c:a aac output.mp4

# Cut from timestamp to timestamp
ffmpeg -i input.mp4 -ss 00:00:30 -to 00:00:45 -c:v libx264 -c:a aac output.mp4

# Stream copy (faster but may lose frames at cut points)
# Only use when source has frequent keyframes
ffmpeg -i input.mp4 -ss 00:00:30 -t 00:00:15 -c copy output.mp4
```

**Note:** Re-encoding is recommended for trimming. Stream copy (`-c copy`) can silently drop video if the seek point doesn't align with a keyframe.

### Speed Up / Slow Down

```bash
# 2x speed (video and audio)
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" -map "[v]" -map "[a]" output.mp4

# 0.5x speed (slow motion)
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=2.0*PTS[v];[0:a]atempo=0.5[a]" -map "[v]" -map "[a]" output.mp4

# Video only (no audio)
ffmpeg -i input.mp4 -filter:v "setpts=0.5*PTS" -an output.mp4
```

### Concatenate Videos

```bash
# Create file list
echo "file 'clip1.mp4'" > list.txt
echo "file 'clip2.mp4'" >> list.txt
echo "file 'clip3.mp4'" >> list.txt

# Concatenate (same codec/resolution)
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

# Concatenate with re-encoding (different sources)
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac output.mp4
```

### Add Fade In/Out

```bash
# Fade in first 1 second, fade out last 1 second (30fps video)
ffmpeg -i input.mp4 -vf "fade=t=in:st=0:d=1,fade=t=out:st=9:d=1" -c:a copy output.mp4

# Audio fade
ffmpeg -i input.mp4 -af "afade=t=in:st=0:d=1,afade=t=out:st=9:d=1" -c:v copy output.mp4
```

### Get Video Info

```bash
# Duration, resolution, codec info
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4

# Full info
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4
```

## Remotion-Specific Patterns

### Video Speed Adjustment for Remotion

**When to use FFmpeg vs Remotion `playbackRate`:**

| Scenario | Use FFmpeg | Use Remotion |
|----------|------------|--------------|
| Constant speed (1.5x, 2x) | Either works | ✅ Simpler |
| Extreme speeds (>4x or <0.25x) | ✅ More reliable | May have issues |
| Variable speed (accelerate over time) | ✅ Pre-process | Complex workaround needed |
| Need perfect audio sync | ✅ Guaranteed | Usually fine |
| Demo needs to fit voiceover timing | ✅ Pre-calculate | Runtime adjustment |

**Remotion limitation:** `playbackRate` must be constant. Dynamic interpolation like `playbackRate={interpolate(frame, [0, 100], [1, 5])}` won't work correctly because Remotion evaluates frames independently.

```bash
# Speed up demo to fit a scene (e.g., 60s demo into 20s = 3x speed)
ffmpeg -i demo-raw.mp4 \
  -filter_complex "[0:v]setpts=0.333*PTS[v];[0:a]atempo=3.0[a]" \
  -map "[v]" -map "[a]" \
  public/demos/demo-fast.mp4

# Slow motion for emphasis (0.5x speed)
ffmpeg -i action.mp4 \
  -filter_complex "[0:v]setpts=2.0*PTS[v];[0:a]atempo=0.5[a]" \
  -map "[v]" -map "[a]" \
  public/demos/action-slow.mp4

# Speed up without audio (common for screen recordings)
ffmpeg -i demo.mp4 -filter:v "setpts=0.5*PTS" -an public/demos/demo-2x.mp4

# Timelapse effect (10x speed, drop audio)
ffmpeg -i long-demo.mp4 -filter:v "setpts=0.1*PTS" -an public/demos/timelapse.mp4
```

**Calculate speed factor:**
- To fit X seconds of video into Y seconds of scene: `speed = X / Y`
- setpts multiplier = `1 / speed` (e.g., 3x speed = setpts=0.333*PTS)
- atempo value = `speed` (e.g., 3x speed = atempo=3.0)

**Extreme speed (>2x audio):** Chain atempo filters (each limited to 0.5-2.0 range):
```bash
# 4x speed audio
-filter_complex "[0:a]atempo=2.0,atempo=2.0[a]"

# 8x speed audio
-filter_complex "[0:a]atempo=2.0,atempo=2.0,atempo=2.0[a]"
```

### Prepare Demo Recording for Remotion

```bash
# Standard 1080p, 30fps, Remotion-ready
ffmpeg -i raw-recording.mp4 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30" \
  -c:v libx264 -crf 18 -preset slow \
  -c:a aac -b:a 192k \
  -movflags faststart \
  public/demos/demo.mp4
```

### Screen Recording to Remotion Asset

```bash
# From iPhone/iPad recording (usually 60fps, variable resolution)
ffmpeg -i iphone-recording.mov \
  -vf "scale=1920:-2,fps=30" \
  -c:v libx264 -crf 20 \
  -an \
  public/demos/mobile-demo.mp4
```

### Batch Convert GIFs

```bash
for f in assets/*.gif; do
  ffmpeg -i "$f" -movflags faststart -pix_fmt yuv420p \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    "public/demos/$(basename "$f" .gif).mp4"
done
```

## Common Issues

### "Height not divisible by 2"
Add scale filter: `-vf "scale=trunc(iw/2)*2:trunc(ih/2)*2"`

### Video won't play in browser
Use: `-movflags faststart -pix_fmt yuv420p -c:v libx264`

### Audio out of sync after speed change
Use filter_complex with atempo: `-filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]"`

### File too large
Increase CRF (23→28) or reduce resolution

## Quality Guidelines

| Use Case | CRF | Preset | Notes |
|----------|-----|--------|-------|
| Archive/Master | 18 | slow | Best quality, large files |
| Production | 20-22 | medium | Good balance |
| Web/Preview | 23-25 | fast | Smaller files |
| Draft/Quick | 28+ | veryfast | Fast encoding |

## Platform-Specific Output Optimization

After Remotion renders your video (typically to `out/video.mp4`), use FFmpeg to optimize for each distribution platform.

### Workflow Integration

```
Remotion render (master)     FFmpeg optimization      Platform upload
       ↓                            ↓                       ↓
   out/video.mp4  ────────→  out/video-youtube.mp4  ───→  YouTube
                  ────────→  out/video-twitter.mp4  ───→  Twitter/X
                  ────────→  out/video-linkedin.mp4 ───→  LinkedIn
                  ────────→  out/video-web.mp4      ───→  Website embed
```

### YouTube (Recommended Settings)

YouTube re-encodes everything, so upload high quality:

```bash
# YouTube optimized (1080p)
ffmpeg -i out/video.mp4 \
  -c:v libx264 -preset slow -crf 18 \
  -profile:v high -level 4.0 \
  -bf 2 -g 30 \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart \
  out/video-youtube.mp4

# YouTube Shorts (vertical 1080x1920)
ffmpeg -i out/video.mp4 \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -crf 18 -c:a aac -b:a 192k \
  out/video-shorts.mp4
```

### Twitter/X

Twitter has strict limits: max 140s, 512MB, 1920x1200:

```bash
# Twitter optimized (under 15MB target for fast upload)
ffmpeg -i out/video.mp4 \
  -c:v libx264 -preset medium -crf 24 \
  -profile:v main -level 3.1 \
  -vf "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease" \
  -c:a aac -b:a 128k -ar 44100 \
  -movflags +faststart \
  -fs 15M \
  out/video-twitter.mp4

# Check file size and duration
ffprobe -v error -show_entries format=duration,size -of csv=p=0 out/video-twitter.mp4
```

### LinkedIn

LinkedIn prefers MP4 with AAC audio, max 10 minutes:

```bash
# LinkedIn optimized
ffmpeg -i out/video.mp4 \
  -c:v libx264 -preset medium -crf 22 \
  -profile:v main \
  -vf "scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease" \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart \
  out/video-linkedin.mp4
```

### Website/Embed (Optimized for Fast Loading)

```bash
# Web-optimized MP4 (small file, progressive loading)
ffmpeg -i out/video.mp4 \
  -c:v libx264 -preset medium -crf 26 \
  -profile:v baseline -level 3.0 \
  -vf "scale=1280:720" \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  out/video-web.mp4

# WebM alternative (better compression, wider browser support)
ffmpeg -i out/video.mp4 \
  -c:v libvpx-vp9 -crf 30 -b:v 0 \
  -vf "scale=1280:720" \
  -c:a libopus -b:a 128k \
  -deadline good \
  out/video-web.webm
```

### GIF (for Previews/Thumbnails)

```bash
# High-quality GIF (first 5 seconds)
ffmpeg -i out/video.mp4 -t 5 \
  -vf "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  out/preview.gif

# Smaller file GIF
ffmpeg -i out/video.mp4 -t 3 \
  -vf "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  out/preview-small.gif
```

### Platform Requirements Quick Reference

| Platform | Max Resolution | Max Size | Max Duration | Audio |
|----------|---------------|----------|--------------|-------|
| YouTube | 8K | 256GB | 12 hours | AAC 48kHz |
| Twitter/X | 1920x1200 | 512MB | 140s | AAC 44.1kHz |
| LinkedIn | 4096x2304 | 5GB | 10 min | AAC 48kHz |
| Instagram Feed | 1080x1350 | 4GB | 60s | AAC 48kHz |
| Instagram Reels | 1080x1920 | 4GB | 90s | AAC 48kHz |
| TikTok | 1080x1920 | 287MB | 10 min | AAC |

### Batch Export for All Platforms

```bash
#!/bin/bash
# save as: export-all-platforms.sh
INPUT="out/video.mp4"

# YouTube (high quality)
ffmpeg -i "$INPUT" -c:v libx264 -preset slow -crf 18 \
  -c:a aac -b:a 192k -movflags +faststart \
  out/video-youtube.mp4

# Twitter (compressed)
ffmpeg -i "$INPUT" -c:v libx264 -crf 24 \
  -vf "scale='min(1280,iw)':'-2'" \
  -c:a aac -b:a 128k -movflags +faststart \
  out/video-twitter.mp4

# LinkedIn
ffmpeg -i "$INPUT" -c:v libx264 -crf 22 \
  -c:a aac -b:a 192k -movflags +faststart \
  out/video-linkedin.mp4

# Web embed (small)
ffmpeg -i "$INPUT" -c:v libx264 -crf 26 \
  -vf "scale=1280:720" \
  -c:a aac -b:a 128k -movflags +faststart \
  out/video-web.mp4

echo "Exported:"
ls -lh out/video-*.mp4
```

## Error Handling

Common errors and fixes when processing video:

```bash
# Check if FFmpeg succeeded
ffmpeg -i input.mp4 -c:v libx264 output.mp4 && echo "Success" || echo "Failed: check input file"

# Validate output file is playable
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 output.mp4

# Get detailed error info
ffmpeg -v error -i input.mp4 -f null - 2>&1 | head -20
```

### Handling Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| "No such file" | Input path wrong | Check path, use quotes for spaces |
| "Invalid data" | Corrupted input | Re-download or re-record source |
| "height not divisible by 2" | Odd dimensions | Add scale filter with trunc |
| "encoder not found" | Missing codec | Install FFmpeg with full codecs |
| Output 0 bytes | Silent failure | Check full ffmpeg output for errors |

---

## Feedback & Contributions

If this skill is missing information or could be improved:

- **Missing a command?** Describe what you needed
- **Found an error?** Let me know what's wrong
- **Want to contribute?** I can help you:
  1. Update this skill with improvements
  2. Create a PR to github.com/digitalsamba/claude-code-video-toolkit

Just say "improve this skill" and I'll guide you through updating `.claude/skills/ffmpeg/SKILL.md`.
