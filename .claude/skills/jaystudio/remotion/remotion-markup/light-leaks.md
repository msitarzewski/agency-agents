---
name: light-leaks
description: Light leak overlay effects for Remotion using lightLeak() from @remotion/effects.
metadata:
  tags: light-leaks, overlays, effects, transitions
---

## Light Leaks

This only works from Remotion 4.0.500 and up. Use `npx remotion versions` to check your Remotion version and `npx remotion upgrade` to upgrade your Remotion version.

Apply `lightLeak()` from `@remotion/effects/light-leak` to a canvas-based component such as `<Solid>`. Animate `progress` from `0` to `1`; the light leak reveals during the first half and retracts during the second half.

Typically use it inside a `<TransitionSeries.Overlay>` to play over the cut point between two scenes. See the **transitions** rule for `<TransitionSeries>` and overlay usage.

## Prerequisites

```bash
npx remotion add @remotion/effects
```

## Light leak overlay component

Keep the `progress` calculation inline so it is editable in Remotion Studio:

```tsx
import {lightLeak} from '@remotion/effects/light-leak';
import {interpolate, Solid, useCurrentFrame, useVideoConfig} from 'remotion';

const LightLeakOverlay: React.FC<{
  seed?: number;
  hueShift?: number;
}> = ({seed = 0, hueShift = 0}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, height, width} = useVideoConfig();

  return (
    <Solid
      width={width}
      height={height}
      effects={[
        lightLeak({
          seed,
          hueShift,
          progress: interpolate(frame, [0, durationInFrames - 1], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }),
      ]}
    />
  );
};
```

## Basic usage with TransitionSeries

```tsx
import {TransitionSeries} from '@remotion/transitions';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={60}>
    <SceneA />
  </TransitionSeries.Sequence>
  <TransitionSeries.Overlay durationInFrames={30}>
    <LightLeakOverlay />
  </TransitionSeries.Overlay>
  <TransitionSeries.Sequence durationInFrames={60}>
    <SceneB />
  </TransitionSeries.Sequence>
</TransitionSeries>;
```

## Options

- `progress?` — controls the evolve/retract phase from `0` to `1`. Effects do not animate on their own, so drive it with `useCurrentFrame()` and `interpolate()`. Default: `0.5`.
- `seed?` — determines the shape of the light leak pattern. Different seeds produce different patterns. Default: `0`.
- `hueShift?` — rotates the hue in degrees (`0`–`360`). Default: `0` (yellow-to-orange). `120` = green, `240` = blue.
- `disabled?` — skips the effect when `true`. Default: `false`.

## Customizing the look

```tsx
// Blue-tinted light leak with a different pattern
<LightLeakOverlay seed={5} hueShift={240} />;

// Green-tinted light leak
<LightLeakOverlay seed={2} hueShift={120} />;
```

## Standalone usage

The overlay component can also be used outside of `<TransitionSeries>` as a decorative layer in any composition:

```tsx
const MyComp: React.FC = () => (
  <>
    <MyContent />
    <LightLeakOverlay seed={3} />
  </>
);
```

`lightLeak()` uses WebGL2. Enable WebGL during rendering with `Config.setChromiumOpenGlRenderer("angle")`.
