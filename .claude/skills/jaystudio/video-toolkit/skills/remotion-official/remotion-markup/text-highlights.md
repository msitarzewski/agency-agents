---
name: text-highlights
description: Animated text highlights and hand-drawn annotations using @remotion/rough-notation.
metadata:
  tags: text, highlights, annotations, circles, rough-notation
---

# Text highlights

Use `@remotion/rough-notation` to draw animated annotations around or behind text. It supports highlights, circles, underlines, strike-throughs, crossed-off text, boxes, and brackets.

Docs: https://www.remotion.dev/docs/text-highlights

Install the package using the same Remotion version as the project:

```bash
bunx remotion add @remotion/rough-notation
```

Choose the component that describes the annotation: `<Highlight>`, `<Circle>`, `<Underline>`, `<StrikeThrough>`, `<CrossedOff>`, `<Box>`, or `<Bracket>`. The component determines both the annotation style and whether it renders behind or on top of the text.

Drive `progress` from `useCurrentFrame()` so the annotation is deterministic and synchronized with the video:

```tsx
import {Circle, Highlight} from '@remotion/rough-notation';
import {interpolate, useCurrentFrame} from 'remotion';

export const TextAnnotations: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div style={{fontSize: 80}}>
      This is{' '}
      <Highlight
        color="rgba(255, 236, 79, 0.62)"
        progress={interpolate(frame, [15, 40], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })}
      >
        important
      </Highlight>
      , and this is{' '}
      <Circle color="#2563eb" progress={interpolate(frame, [15, 40], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })}>
        connected
      </Circle>
      .
    </div>
  );
};
```

Keep `progress` inline, hardcoded and use `interpolate` for maximum [Studio interactivity](../remotion-interactivity/REFERENCE.md).
