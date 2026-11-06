---
name: color-correction
description: Correct exposure, white balance, and tone with primary adjustments, Levels, Curves, and 3D Cube LUTs.
metadata:
  tags: color-correction, color-grading, levels, curves, lut, cube, exposure, white-balance
---

# Color correction

Apply color adjustments through the `effects` prop of `<Video>` from `@remotion/media`, or other supported components.  
See [effects.md](effects.md) for more context on effects.

## Primary adjustments

Prefer [`colorCorrection()`](https://www.remotion.dev/docs/effects/color-correction) when combining adjustments.  
It performs them in one WebGL pass and exposes controls in the Studio.

| Control                 | Meaning and range                                                         | Neutral value |
| ----------------------- | ------------------------------------------------------------------------- | ------------- |
| `exposure`              | Stops, from `-5` to `5`; positive values brighten                         | `0`           |
| `temperature`           | From `-1` (cooler) to `1` (warmer)                                        | `0`           |
| `tint`                  | From `-1` (greener) to `1` (more magenta)                                 | `0`           |
| `shadows`, `highlights` | From `-1` to `1`; negative values darken, positive values lift the region | `0`           |
| `blacks`, `whites`      | From `-1` to `1`; target narrower regions near black and white            | `0`           |
| `contrast`              | Non-negative multiplier around `pivot` (`0` to `1`, default `0.5`)        | `1`           |
| `saturation`            | Non-negative multiplier; `0` is grayscale                                 | `1`           |
| `vibrance`              | From `-1` to `1`; positive values emphasize muted colors                  | `0`           |

```tsx
import {colorCorrection} from '@remotion/effects/color-correction';
import {Video} from '@remotion/media';
import {staticFile} from 'remotion';

export const CorrectedVideo = () => {
  return (
    <Video
      src={staticFile('footage.mp4')}
      effects={[
        colorCorrection({
          exposure: 0.25,
          temperature: 0.1,
          tint: -0.03,
          shadows: 0.15,
          highlights: -0.1,
          contrast: 1.1,
          saturation: 1.05,
          vibrance: 0.15,
        }),
      ]}
    />
  );
};
```

Internally, `colorCorrection()` applies exposure, white balance, tonal regions,
contrast, saturation, then vibrance. Omitted controls use their neutral values.
Keep everything inline on the target's `effects` prop.

Standalone effects are also available when a different order or an additional
adjustment is needed: `exposure()`, `whiteBalance()`, `shadowsHighlights()`,
`contrast()`, `saturation()`, and `vibrance()`. See [effects](effects.md)

## Levels and Curves

Use [`levels()`](https://www.remotion.dev/docs/effects/levels) to set input black
and white points, adjust midtones with gamma, or limit the output range.
`blackPoint` and `whitePoint` are normalized from `0` to `1`, default to `0` and
`1`, and require `blackPoint < whitePoint`. `gamma` ranges from `0.01` to `10`,
defaults to `1`, and values above `1` brighten midtones. `outputBlack` and
`outputWhite` range from `0` to `1` and default to `0` and `1`; reversing them
inverts the output.

Use [`curves()`](https://www.remotion.dev/docs/effects/curves) for an S-curve or
other adjustments that need multiple input/output control points. Supply `2` to
`32` `[input, output]` pairs with both coordinates in `0` to `1` and strictly
increasing input values. Outputs may increase or decrease. The default
`[[0, 0], [1, 1]]` leaves the image unchanged. Values outside the first and last
input points use the nearest endpoint's output.

Curves uses `interpolation: 'smooth'` by default, connecting points without
overshooting their output values. Use `'linear'` for straight segments.
`amount` blends with the original image from `0` to `1` (default `1`).

Both effects default to `channel: 'rgb'`. Set `'red'`, `'green'`, or `'blue'` to
adjust one channel, and stack separate effect calls for different channel
adjustments. Both preserve alpha. Curves, the Levels channel/output controls,
and their graphical Studio editors are available from Remotion `4.0.537`.

Keep the effect calls and point arrays inline so Studio can edit them:

```tsx
import {curves} from '@remotion/effects/curves';
import {levels} from '@remotion/effects/levels';
import {Video} from '@remotion/media';
import {staticFile} from 'remotion';

export const ToneAdjustedVideo = () => {
  return (
    <Video
      src={staticFile('footage.mp4')}
      effects={[
        levels({
          blackPoint: 0.03,
          whitePoint: 0.95,
          gamma: 1.1,
          outputBlack: 0.02,
          outputWhite: 0.98,
        }),
        curves({
          channel: 'red',
          points: [[0, 0], [0.5, 0.55], [1, 1]],
          amount: 0.8,
        }),
      ]}
    />
  );
};
```

Effects run in array order: this example adjusts the RGB levels, then lifts
red midtones. Place primary adjustments before `lut()` when the LUT should
receive the corrected footage.

## LUTs and combining effects

A LUT (lookup table) maps input RGB colors to output colors. Use
[`lut()`](https://www.remotion.dev/docs/effects/lut) to apply a 3D `.cube` LUT.  
Its `content` parameter takes the complete file contents as a string.

This example uses a small warm LUT inline:

```tsx
import {colorCorrection} from '@remotion/effects/color-correction';
import {lut} from '@remotion/effects/lut';
import {Video} from '@remotion/media';
import {staticFile} from 'remotion';

export const GradedVideo = () => {
  return (
    <Video
      src={staticFile('footage.mp4')}
      effects={[
        colorCorrection({exposure: 0.25, contrast: 1.1}),
        lut({
          content: `TITLE "Warm"
LUT_3D_SIZE 2
0 0 0
1 0.1 0
0 0.9 0.1
1 0.9 0.1
0 0.1 0.8
1 0.2 0.7
0 0.9 0.8
1 0.9 0.8`,
        }),
      ]}
    />
  );
};
```

### Supported format and limitations

- Only 3D `.cube` LUTs are supported. `LUT_3D_SIZE` must be an integer from `2`
  to `256`, followed by exactly `size ** 3` RGB rows. 1D LUTs are unsupported.
- Optional `TITLE`, `DOMAIN_MIN`, `DOMAIN_MAX`, blank lines, and `#` comments are
  supported. Other LUT formats need conversion before use.
- `lut()` has no `src` or strength/amount parameter. Use `disabled: true` to
  bypass it.

## Studio workflow

Select the layer and open its effect in the inspector. Levels shows an input
histogram with black, gamma, and white input handles plus output endpoints.
Curves shows an input histogram behind the graph: add or drag points, edit
their numeric coordinates, remove points, or reset the curve. The histogram
shows pixels entering that effect, including adjustments earlier in the stack.

Levels numeric controls and Curves `amount` can be keyframed in Studio.
Curves points are not keyframable in Studio. To animate them, derive `points`
from `useCurrentFrame()` in code, keeping input values strictly increasing on
every frame. Computed point arrays display as read-only in the graph.

Put `.cube` files in `public/` to preview them in the Assets panel.  
The user can drag a 3D `.cube` file from the computer or Assets panel onto a
video in the canvas or timeline to apply the LUT effect.

## See also

- [Color correction documentation](https://www.remotion.dev/docs/color-correction)
