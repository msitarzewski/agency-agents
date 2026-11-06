---
name: get-audio-duration
description: Getting the duration of an audio file in seconds with Mediabunny
metadata:
  tags: duration, audio, length, time, seconds, mp3, wav
---

# Getting audio duration with Mediabunny

Mediabunny can extract the duration of an audio file. It works in browser, Node.js, and Bun environments.

## Getting audio duration

```tsx title="get-audio-duration.ts"
import { Input, ALL_FORMATS, UrlSource } from "mediabunny";

export const getAudioDuration = async (src: string) => {
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
const duration = await getAudioDuration("https://remotion.media/audio.mp3");
console.log(duration); // e.g. 180.5 (seconds)
```

## Using with staticFile in Remotion

Make sure to wrap the file path in `staticFile()`:

```tsx
import { staticFile } from "remotion";

const duration = await getAudioDuration(staticFile("audio.mp3"));
```

## In Node.js and Bun

Use `FilePathSource` instead of `UrlSource` to read a file from disk:

```tsx
import { Input, ALL_FORMATS, FilePathSource } from "mediabunny";

const input = new Input({
  formats: ALL_FORMATS,
  source: new FilePathSource("audio.mp3"),
});

const durationInSeconds = await input.computeDuration();
input.dispose(); // Closes the file handle
```

For a `File` from a file input or drag and drop, use `new BlobSource(file)` instead.
