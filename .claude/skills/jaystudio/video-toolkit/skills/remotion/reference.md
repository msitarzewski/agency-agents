# Remotion API Reference

## Core Hooks

### useCurrentFrame()
```tsx
const frame = useCurrentFrame();
```
Returns current frame (0-indexed). Inside `<Sequence>`, returns relative frame.

### useVideoConfig()
```tsx
const { width, height, fps, durationInFrames, id, defaultProps } = useVideoConfig();
```

## interpolate()

```tsx
interpolate(
  input: number,
  inputRange: number[],
  outputRange: number[],
  options?: {
    extrapolateLeft?: 'extend' | 'clamp' | 'identity' | 'wrap',
    extrapolateRight?: 'extend' | 'clamp' | 'identity' | 'wrap',
    easing?: (t: number) => number
  }
): number
```

**Examples:**
```tsx
// Basic interpolation
interpolate(15, [0, 30], [0, 100]); // 50

// With clamping
interpolate(50, [0, 30], [0, 1], { extrapolateRight: 'clamp' }); // 1

// Multiple keyframes
interpolate(frame, [0, 20, 40, 60], [0, 1, 1, 0]);

// With easing
interpolate(frame, [0, 30], [0, 100], { easing: Easing.bezier(0.42, 0, 0.58, 1) });
```

## spring()

```tsx
spring({
  frame: number,
  fps: number,
  config?: {
    damping?: number,      // Default: 10
    mass?: number,         // Default: 1  
    stiffness?: number,    // Default: 100
    overshootClamping?: boolean
  },
  from?: number,           // Default: 0
  to?: number,             // Default: 1
  durationInFrames?: number,
  durationRestThreshold?: number,
  delay?: number,
  reverse?: boolean
}): number
```

**Config presets:**
- High bounce: `{ damping: 5, stiffness: 200 }`
- No bounce: `{ damping: 20, stiffness: 100, overshootClamping: true }`
- Slow: `{ damping: 20, mass: 2 }`

## measureSpring()

Get the duration of a spring animation:
```tsx
import { measureSpring } from 'remotion';

const duration = measureSpring({ fps: 30, config: { damping: 10 } });
// Returns number of frames until spring settles
```

## interpolateColors()

```tsx
interpolateColors(
  input: number,
  inputRange: number[],
  outputRange: string[],  // Hex, rgb(), rgba(), hsl()
  options?: { extrapolateLeft?, extrapolateRight? }
): string
```

## Easing

```tsx
import { Easing } from 'remotion';

// Basic
Easing.linear
Easing.ease
Easing.quad
Easing.cubic

// In/Out/InOut variants
Easing.in(Easing.quad)
Easing.out(Easing.cubic)
Easing.inOut(Easing.ease)

// Cubic bezier
Easing.bezier(x1, y1, x2, y2)

// Other
Easing.circle
Easing.back(s?)      // Overshoot
Easing.elastic(bounciness?)
Easing.bounce
Easing.sin
Easing.exp
Easing.poly(n)       // Power of n
```

## Components

### Composition
```tsx
<Composition
  id="MyVideo"
  component={MyComponent}
  // OR lazyComponent={() => import('./MyComponent')}
  durationInFrames={150}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{ title: 'Hello' }}
  calculateMetadata={async ({ props }) => ({
    durationInFrames: props.items.length * 30,
    props: { ...props, computed: true }
  })}
/>
```

### Sequence
```tsx
<Sequence
  from={30}                    // Start frame
  durationInFrames={60}        // Optional duration
  name="Intro"                 // Label in Studio timeline
  layout="none"                // "none" | "absolute-fill"
>
  <Child />
</Sequence>
```

### Series
```tsx
<Series>
  <Series.Sequence durationInFrames={30} offset={-5}>
    <A />  {/* Frames 0-29 */}
  </Series.Sequence>
  <Series.Sequence durationInFrames={60}>
    <B />  {/* Frames 25-84 (offset caused overlap) */}
  </Series.Sequence>
</Series>
```

### Loop
```tsx
<Loop
  durationInFrames={30}
  times={3}                    // Or Infinity
  layout="none"
>
  <Animation />
</Loop>
```

### AbsoluteFill
```tsx
<AbsoluteFill style={{ backgroundColor: '#000' }}>
  {/* Position: absolute, full width/height */}
</AbsoluteFill>
```

### Media Components

**Img** (waits for load):
```tsx
<Img src={staticFile('photo.jpg')} style={{ width: '100%' }} />
```

**Video/Html5Video:**
```tsx
<Video
  src={staticFile('clip.mp4')}
  volume={0.5}                 // 0-1, or callback: (f) => f / 100
  playbackRate={1.5}
  muted={false}
  loop={false}
  startFrom={30}               // Skip first 30 frames of source
  endAt={120}                  // Stop at frame 120 of source
  acceptableTimeShiftInSeconds={0.2}
/>
```

**OffthreadVideo** (better performance):
```tsx
<OffthreadVideo
  src={staticFile('clip.mp4')}
  volume={0.5}
  transparent={false}          // For videos with alpha
  toneMapped={true}           // HDR tone mapping
/>
```

**Audio:**
```tsx
<Audio
  src={staticFile('music.mp3')}
  volume={0.8}
  startFrom={0}
  endAt={300}
  playbackRate={1}
/>
```

**AnimatedImage** (GIF/APNG):
```tsx
<AnimatedImage src={staticFile('animation.gif')} />
```

## Async Handling

```tsx
import { delayRender, continueRender, cancelRender } from 'remotion';

// Block render
const handle = delayRender('Loading data...');

// Unblock when ready
continueRender(handle);

// Cancel on error
cancelRender(new Error('Failed to load'));
```

**With timeout:**
```tsx
const handle = delayRender('Loading...', { timeoutInMilliseconds: 30000 });
```

## Static Files & Prefetching

```tsx
import { staticFile, prefetch, getStaticFiles } from 'remotion';

// Reference file in public/
const url = staticFile('video.mp4');

// Prefetch for faster playback
const { free, waitUntilDone } = prefetch(url);
await waitUntilDone();
// Later: free() to release memory

// List all static files
const files = getStaticFiles();  // ['video.mp4', 'image.png', ...]
```

## Input Props

```tsx
import { getInputProps } from 'remotion';

const props = getInputProps();  // Data passed via --props CLI flag
```

## Environment Detection

```tsx
import { getRemotionEnvironment } from 'remotion';

const env = getRemotionEnvironment();
// { isStudio: boolean, isRendering: boolean, isPlayer: boolean }
```

## random()

Deterministic random for consistent renders:
```tsx
import { random } from 'remotion';

const value = random('my-seed');      // 0-1, same every render
const value2 = random('seed', 0, 100); // 0-100
const value3 = random(null);           // Different each render
```

## @remotion/renderer API

```tsx
import { bundle } from '@remotion/bundler';
import { 
  renderMedia, 
  renderStill,
  selectComposition,
  getCompositions,
  renderFrames,
  stitchFramesToVideo
} from '@remotion/renderer';

// Bundle project
const bundleLocation = await bundle({
  entryPoint: './src/index.ts',
  webpackOverride: (config) => config,
});

// Get composition
const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: 'MyComp',
  inputProps: {},
});

// Render video
await renderMedia({
  composition,
  serveUrl: bundleLocation,
  codec: 'h264',              // h264, h265, vp8, vp9, gif, prores
  outputLocation: 'out.mp4',
  inputProps: {},
  onProgress: ({ progress }) => console.log(`${progress * 100}%`),
  imageFormat: 'jpeg',        // jpeg or png
  jpegQuality: 80,
  scale: 1,
  frameRange: [0, 59],        // Optional: specific frames
  muted: false,
  audioBitrate: '128k',
  videoBitrate: '5M',
  crf: 18,                    // Quality (lower = better, bigger)
  concurrency: 4,
});

// Render still image
await renderStill({
  composition,
  serveUrl: bundleLocation,
  output: 'thumbnail.png',
  frame: 30,
  imageFormat: 'png',
});
```

## @remotion/lambda API

```tsx
import {
  deployFunction,
  deploySite,
  renderMediaOnLambda,
  renderStillOnLambda,
  getRenderProgress,
  downloadMedia,
} from '@remotion/lambda';

// Deploy function
const { functionName } = await deployFunction({
  region: 'us-east-1',
  timeoutInSeconds: 120,
  memorySizeInMb: 2048,
});

// Deploy site
const { serveUrl } = await deploySite({
  entryPoint: './src/index.ts',
  region: 'us-east-1',
  siteName: 'my-video',
});

// Render
const { renderId, bucketName } = await renderMediaOnLambda({
  region: 'us-east-1',
  functionName,
  serveUrl,
  composition: 'MyComp',
  codec: 'h264',
  inputProps: {},
  framesPerLambda: 20,
});

// Check progress
const progress = await getRenderProgress({
  renderId,
  bucketName,
  region: 'us-east-1',
  functionName,
});

// Download when done
if (progress.done) {
  await downloadMedia({
    bucketName,
    renderId,
    region: 'us-east-1',
    outPath: 'video.mp4',
  });
}
```

## @remotion/player API

```tsx
import { Player, PlayerRef } from '@remotion/player';

const playerRef = useRef<PlayerRef>(null);

<Player
  ref={playerRef}
  component={MyComp}
  // OR lazyComponent={() => import('./MyComp')}
  durationInFrames={150}
  fps={30}
  compositionWidth={1920}
  compositionHeight={1080}
  inputProps={{}}
  style={{ width: '100%' }}
  controls={true}
  autoPlay={false}
  loop={false}
  showVolumeControls={true}
  allowFullscreen={true}
  clickToPlay={true}
  doubleClickToFullscreen={true}
  spaceKeyToPlayOrPause={true}
  playbackRate={1}
  renderLoading={() => <div>Loading...</div>}
  errorFallback={({ error }) => <div>Error: {error.message}</div>}
  numberOfSharedAudioTags={5}
  initiallyShowControls={3000}
  renderPlayPauseButton={() => null}
  moveToBeginningWhenEnded={true}
/>

// Imperative API
playerRef.current?.play();
playerRef.current?.pause();
playerRef.current?.toggle();
playerRef.current?.seekTo(30);
playerRef.current?.getCurrentFrame();
playerRef.current?.isPlaying();
playerRef.current?.getVolume();
playerRef.current?.setVolume(0.5);
playerRef.current?.isMuted();
playerRef.current?.mute();
playerRef.current?.unmute();
playerRef.current?.requestFullscreen();
playerRef.current?.exitFullscreen();
playerRef.current?.isFullscreen();

// Events
<Player
  onPlay={() => {}}
  onPause={() => {}}
  onEnded={() => {}}
  onError={(e) => {}}
  onSeeked={(frame) => {}}
  onTimeUpdate={({ frame }) => {}}
  onFullscreenChange={(isFullscreen) => {}}
/>
```

## calculateMetadata

Dynamic composition properties:
```tsx
export const calculateMetadata: CalculateMetadataFunction<Props> = async ({ 
  props, 
  abortSignal, 
  defaultProps 
}) => {
  const data = await fetch('/api/data', { signal: abortSignal });
  
  return {
    durationInFrames: data.items.length * 30,
    fps: 60,
    width: 1920,
    height: 1080,
    props: { ...props, items: data.items },
  };
};

<Composition
  id="Dynamic"
  component={MyComp}
  calculateMetadata={calculateMetadata}
  // Base values (can be overridden by calculateMetadata)
  durationInFrames={1}
  fps={30}
  width={1920}
  height={1080}
/>
```
