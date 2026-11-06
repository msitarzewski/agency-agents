---
name: get-video-dimensions
description: Getting the width and height of a video file with Mediabunny
metadata:
  tags: dimensions, width, height, resolution, size, video
---

# Getting video dimensions with Mediabunny

Mediabunny can extract the width and height of a video file. It works in browser, Node.js, and Bun environments.

## Getting video dimensions

```tsx
import { Input, ALL_FORMATS, UrlSource } from "mediabunny";

export const getVideoDimensions = async (src: string) => {
  const input = new Input({
    formats: ALL_FORMATS,
    source: new UrlSource(src),
  });

  const videoTrack = await input.getPrimaryVideoTrack();
  if (!videoTrack) {
    throw new Error("No video track found");
  }

  return {
    width: videoTrack.displayWidth,
    height: videoTrack.displayHeight,
  };
};
```

## Usage

```tsx
const dimensions = await getVideoDimensions("https://remotion.media/video.mp4");
console.log(dimensions.width); // e.g. 1920
console.log(dimensions.height); // e.g. 1080
```

## Using with local files

For a `File` from a file input or drag and drop, use `BlobSource` instead of `UrlSource`:

```tsx
import { Input, ALL_FORMATS, BlobSource } from "mediabunny";

const input = new Input({
  formats: ALL_FORMATS,
  source: new BlobSource(file), // File object from input or drag-drop
});

const videoTrack = await input.getPrimaryVideoTrack();
if (!videoTrack) {
  throw new Error("No video track found");
}

const width = videoTrack.displayWidth;
const height = videoTrack.displayHeight;
```

In Node.js and Bun, use `new FilePathSource(path)` to read a file from disk, and call `input.dispose()` when done.

## Using with staticFile in Remotion

```tsx
import { staticFile } from "remotion";

const dimensions = await getVideoDimensions(staticFile("video.mp4"));
```
