---
name: get-video-duration
description: Getting the duration of a video file in seconds with Mediabunny
metadata:
  tags: duration, video, length, time, seconds
---

# Getting video duration with Mediabunny

Mediabunny can extract the duration of a video file. It works in browser, Node.js, and Bun environments.

## Getting video duration

```tsx
import { Input, ALL_FORMATS, UrlSource } from "mediabunny";

export const getVideoDuration = async (src: string) => {
  const input = new Input({
    formats: ALL_FORMATS,
    source: new UrlSource(src),
  });

  const durationInSeconds = await input.computeDuration();
  return durationInSeconds;
};
```

## Usage

```tsx
const duration = await getVideoDuration("https://remotion.media/video.mp4");
console.log(duration); // e.g. 10.5 (seconds)
```

## Video files from the public/ directory

Make sure to wrap the file path in `staticFile()`:

```tsx
import { staticFile } from "remotion";

const duration = await getVideoDuration(staticFile("video.mp4"));
```

## In Node.js and Bun

Use `FilePathSource` instead of `UrlSource` to read a file from disk:

```tsx
import { Input, ALL_FORMATS, FilePathSource } from "mediabunny";

const input = new Input({
  formats: ALL_FORMATS,
  source: new FilePathSource("video.mp4"),
});

const durationInSeconds = await input.computeDuration();
input.dispose(); // Closes the file handle
```

For a `File` from a file input or drag and drop, use `new BlobSource(file)` instead.
