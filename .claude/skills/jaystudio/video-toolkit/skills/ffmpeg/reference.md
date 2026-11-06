# FFmpeg Reference

## Filter Syntax

### Video Filters (-vf)

```bash
# Chain filters with comma
-vf "scale=1920:1080,fps=30,crop=1280:720"

# Complex filters with labels
-filter_complex "[0:v]scale=1920:1080[scaled];[scaled]fps=30[out]" -map "[out]"
```

### Common Video Filters

| Filter | Syntax | Example |
|--------|--------|---------|
| scale | `scale=w:h` | `scale=1920:1080` or `scale=1280:-1` (auto height) |
| crop | `crop=w:h:x:y` | `crop=1280:720:320:180` |
| fps | `fps=N` | `fps=30` |
| pad | `pad=w:h:x:y:color` | `pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black` |
| fade | `fade=t=in/out:st=N:d=N` | `fade=t=in:st=0:d=1` |
| setpts | `setpts=N*PTS` | `setpts=0.5*PTS` (2x speed) |
| drawtext | `drawtext=text='Hi':fontsize=24` | Add text overlay |
| overlay | `overlay=x:y` | Combine videos |

### Common Audio Filters (-af)

| Filter | Syntax | Example |
|--------|--------|---------|
| volume | `volume=N` | `volume=1.5` or `volume=0.5` |
| afade | `afade=t=in/out:st=N:d=N` | `afade=t=in:st=0:d=1` |
| atempo | `atempo=N` | `atempo=2.0` (2x speed, range 0.5-2.0) |
| loudnorm | `loudnorm` | Normalize audio levels |

## Codec Options

### Video Codecs (-c:v)

| Codec | Use Case | Notes |
|-------|----------|-------|
| libx264 | Universal H.264 | Best compatibility |
| libx265 | H.265/HEVC | Better compression, less compatible |
| libvpx-vp9 | WebM | Good for web |
| prores | ProRes | Professional editing |
| copy | Stream copy | No re-encoding, fastest |

### Audio Codecs (-c:a)

| Codec | Use Case | Notes |
|-------|----------|-------|
| aac | MP4 container | Most compatible |
| libmp3lame | MP3 | Universal |
| libvorbis | WebM/OGG | Open source |
| pcm_s16le | WAV | Uncompressed |
| copy | Stream copy | No re-encoding |

## Quality Settings

### CRF (Constant Rate Factor) for x264/x265

| CRF | Quality | Use Case |
|-----|---------|----------|
| 0 | Lossless | Archive |
| 17-18 | Visually lossless | Master |
| 19-22 | High quality | Production |
| 23 | Default | General use |
| 24-27 | Medium | Web delivery |
| 28+ | Low | Preview/draft |

### Presets (-preset)

Faster presets = larger files, quicker encoding

`ultrafast` → `superfast` → `veryfast` → `faster` → `fast` → `medium` → `slow` → `slower` → `veryslow`

## Container Formats

| Format | Extension | Best For |
|--------|-----------|----------|
| MP4 | .mp4 | Universal, web, mobile |
| MOV | .mov | Apple ecosystem, ProRes |
| WebM | .webm | Web (VP9) |
| MKV | .mkv | Archive, multiple streams |
| GIF | .gif | Short animations (no audio) |

## Input/Output Options

### Input Options (before -i)

| Option | Purpose | Example |
|--------|---------|---------|
| -ss | Seek to time | `-ss 00:01:30` |
| -t | Duration limit | `-t 00:00:30` |
| -r | Input framerate | `-r 30` |
| -f | Force format | `-f gif` |

### Output Options (after -i)

| Option | Purpose | Example |
|--------|---------|---------|
| -y | Overwrite output | `-y` |
| -n | Never overwrite | `-n` |
| -movflags faststart | Web streaming | `-movflags faststart` |
| -pix_fmt | Pixel format | `-pix_fmt yuv420p` |
| -an | No audio | `-an` |
| -vn | No video | `-vn` |

## Useful Patterns

### Get Duration in Seconds

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 input.mp4
```

### Get Resolution

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 input.mp4
```

### Get Frame Count

```bash
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -of csv=p=0 input.mp4
```

### Create Thumbnail

```bash
# At specific time
ffmpeg -i input.mp4 -ss 00:00:05 -vframes 1 thumbnail.jpg

# Best quality
ffmpeg -i input.mp4 -ss 00:00:05 -vframes 1 -q:v 2 thumbnail.jpg
```

### Create GIF from Video

```bash
# Simple (large file)
ffmpeg -i input.mp4 -vf "fps=10,scale=480:-1" output.gif

# With palette (better quality, smaller)
ffmpeg -i input.mp4 -vf "fps=10,scale=480:-1,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif
```

### Picture-in-Picture

```bash
# Overlay small video in corner
ffmpeg -i main.mp4 -i overlay.mp4 \
  -filter_complex "[1:v]scale=320:-1[pip];[0:v][pip]overlay=W-w-20:H-h-20" \
  -c:a copy output.mp4
```

### Side-by-Side Videos

```bash
ffmpeg -i left.mp4 -i right.mp4 \
  -filter_complex "[0:v][1:v]hstack=inputs=2[v]" \
  -map "[v]" -c:v libx264 output.mp4
```

## Remotion Integration Notes

- Remotion uses `<OffthreadVideo>` which handles most formats
- Prefer H.264 (libx264) in MP4 container
- Always use `-movflags faststart` for web playback
- Match fps to composition (usually 30fps)
- Resolution should match composition (1920x1080 typical)
