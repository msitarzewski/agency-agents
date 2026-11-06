---
name: transitions
description: Scene transitions and overlays for Remotion using TransitionSeries.
metadata:
  tags: transitions, overlays, fade, slide, wipe, scenes
---

## TransitionSeries

`<TransitionSeries>` arranges scenes and supports two ways to enhance the cut point between them:

- **Transitions** (`<TransitionSeries.Transition>`) — crossfade, slide, wipe, etc. between two scenes. Shortens the timeline because both scenes play simultaneously during the transition.
- **Overlays** (`<TransitionSeries.Overlay>`) — render an effect (e.g. a light leak) on top of the cut point without shortening the timeline.

For a multi-scene timeline, keep the outer `<TransitionSeries>` visible in the
timeline. Studio favors the active scene sequence when the two have the same
full-frame canvas outline.

Children are absolutely positioned.

## Prerequisites

```bash
bunx remotion add @remotion/transitions
```

## Transition example

Use the connected `Chapter` scene from the
[composition example](../remotion-interactivity/timeline-structure.md).

```tsx title="TransitionVideo.tsx"
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {Chapter} from './Chapter';

export const TransitionVideo = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence name="Opening" durationInFrames={60}>
      <Chapter title="Introduction" style={{backgroundColor: '#111111'}} />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition
      presentation={fade()}
      timing={linearTiming({durationInFrames: 15})}
    />
    <TransitionSeries.Sequence name="Feature" durationInFrames={60}>
      <Chapter title="New features" style={{backgroundColor: '#243b53'}} />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);
```

## Custom presentation

```tsx title="SlideInPresentation.tsx"
import type {TransitionPresentationComponentProps} from '@remotion/transitions';

export const SlideInPresentation = ({
  children,
  presentationDirection,
  presentationProgress,
}: TransitionPresentationComponentProps<Record<string, never>>) => {
  if (presentationDirection === 'exiting') {
    return <>{children}</>;
  }

  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          translate: `${(1 - presentationProgress) * 100}% 0`,
        }}
      >
        {children}
      </div>
    </div>
  );
};
```

Use it in place of `fade()` in `TransitionVideo.tsx`:

```tsx
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {SlideInPresentation} from './SlideInPresentation';

<TransitionSeries.Transition
  presentation={{component: SlideInPresentation, props: {}}}
  timing={linearTiming({durationInFrames: 15})}
/>;
```

## Overlay example

```tsx title="LightLeakOverlay.tsx"
import {lightLeak} from '@remotion/effects/light-leak';
import type {CSSProperties} from 'react';
import {Interactive, interpolate, Solid, useCurrentFrame, useVideoConfig} from 'remotion';

const LightLeakOverlayInner = ({style}: {readonly style?: CSSProperties}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, height, width} = useVideoConfig();

  return (
    <Solid
      width={width}
      height={height}
      style={style}
      effects={[
        lightLeak({
          progress: interpolate(frame, [0, durationInFrames - 1], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }),
      ]}
    />
  );
};

export const LightLeakOverlay = Interactive.create({
  Component: LightLeakOverlayInner,
  layout: 'none',
});
```

```tsx title="OverlayVideo.tsx"
import {TransitionSeries} from '@remotion/transitions';
import {Chapter} from './Chapter';
import {LightLeakOverlay} from './LightLeakOverlay';

export const OverlayVideo = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence name="Opening" durationInFrames={60}>
      <Chapter title="Introduction" style={{backgroundColor: '#111111'}} />
    </TransitionSeries.Sequence>
    <TransitionSeries.Overlay durationInFrames={20}>
      <LightLeakOverlay name="Light leak" />
    </TransitionSeries.Overlay>
    <TransitionSeries.Sequence name="Feature" durationInFrames={60}>
      <Chapter title="New features" style={{backgroundColor: '#243b53'}} />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);
```

## Mixing transitions and overlays

Separate overlays and transitions with a scene.

```tsx title="MixedVideo.tsx"
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {Chapter} from './Chapter';
import {LightLeakOverlay} from './LightLeakOverlay';

export const MixedVideo = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence name="Opening" durationInFrames={60}>
      <Chapter title="Introduction" style={{backgroundColor: '#111111'}} />
    </TransitionSeries.Sequence>
    <TransitionSeries.Overlay durationInFrames={30}>
      <LightLeakOverlay name="Light leak" />
    </TransitionSeries.Overlay>
    <TransitionSeries.Sequence name="Feature" durationInFrames={60}>
      <Chapter title="New features" style={{backgroundColor: '#243b53'}} />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition
      presentation={fade()}
      timing={linearTiming({durationInFrames: 15})}
    />
    <TransitionSeries.Sequence name="Closing" durationInFrames={60}>
      <Chapter title="Thank you" style={{backgroundColor: '#382345'}} />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);
```

## Transition props

`<TransitionSeries.Transition>` requires:

- `presentation` — the visual effect (e.g. `fade()`, `slide()`, `wipe()`).
- `timing` — controls speed and easing (e.g. `linearTiming()`, `springTiming()`).

## Overlay props

`<TransitionSeries.Overlay>` accepts:

- `durationInFrames` — how long the overlay is visible (positive integer).
- `offset?` — shifts the overlay relative to the cut point center. Positive = later, negative = earlier. Default: `0`.

## Available transition types

Import transitions from their respective modules:

```tsx
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { clockWipe } from "@remotion/transitions/clock-wipe";
```

## Slide transition with direction

```tsx
import {TransitionSeries, linearTiming} from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";

<TransitionSeries.Transition
  presentation={slide({ direction: "from-left" })}
  timing={linearTiming({ durationInFrames: 20 })}
/>;
```

Directions: `"from-left"`, `"from-right"`, `"from-top"`, `"from-bottom"`

## Timing options

```tsx
import { linearTiming, springTiming } from "@remotion/transitions";

// Linear timing - constant speed
linearTiming({ durationInFrames: 20 });

// Spring timing - organic motion
springTiming({ config: { damping: 200 }, durationInFrames: 25 });
```

## Duration calculation

Transitions overlap adjacent scenes, so the total composition length is **shorter** than the sum of all sequence durations. Overlays do **not** affect the total duration.

For example, with two 60-frame sequences and a 15-frame transition:

- Without transitions: `60 + 60 = 120` frames
- With transition: `60 + 60 - 15 = 105` frames

Adding an overlay between two other sequences does not change the total.

### Getting the duration of a transition

Use the `getDurationInFrames()` method on the timing object:

```tsx
import { linearTiming, springTiming } from "@remotion/transitions";

const linearDuration = linearTiming({
  durationInFrames: 20,
}).getDurationInFrames({ fps: 30 });
// Returns 20

const springDuration = springTiming({
  config: { damping: 200 },
}).getDurationInFrames({ fps: 30 });
// Returns calculated duration based on spring physics
```

For `springTiming` without an explicit `durationInFrames`, the duration depends on `fps` because it calculates when the spring animation settles.

### Calculating total composition duration

```tsx
import { linearTiming } from "@remotion/transitions";

const scene1Duration = 60;
const scene2Duration = 60;
const scene3Duration = 60;

const timing1 = linearTiming({ durationInFrames: 15 });
const timing2 = linearTiming({ durationInFrames: 20 });

const transition1Duration = timing1.getDurationInFrames({ fps: 30 });
const transition2Duration = timing2.getDurationInFrames({ fps: 30 });

const totalDuration =
  scene1Duration +
  scene2Duration +
  scene3Duration -
  transition1Duration -
  transition2Duration;
// 60 + 60 + 60 - 15 - 20 = 145 frames
```
