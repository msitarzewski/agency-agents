# Motion blur

Use `@remotion/motion-blur` for frame-driven motion blur.  
Install it with `npx remotion add @remotion/motion-blur`.

`<HtmlInCanvasMotionBlur>` is the state of the art in Remotion for blurring animated HTML. It captures the content at fractional frames and averages its pixels in a canvas.

## `<HtmlInCanvasMotionBlur>`

Available from Remotion 4.0.529.  
Supply the canvas `width` and `height`, usually from `useVideoConfig()`.  
`shutterAngle` defaults to `180` and accepts `0` to `360`.
`0` disables blur. `samples` defaults to `8` and must be an integer from `1` to `64`. More samples can smooth the blur but increase preview and render cost.

Call `useCurrentFrame()` inside the child component so each sample receives its own frame.

```tsx
import {
  HtmlInCanvasMotionBlur,
} from '@remotion/motion-blur';
import {useCurrentFrame, useVideoConfig} from 'remotion';

const MovingBox = () => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        left: frame * 10,
        top: 200,
        width: 120,
        height: 120,
        backgroundColor: '#ff6b6b',
      }}
    />
  );
};

export const HtmlInCanvasBlur = () => {
  const {width, height} = useVideoConfig();

  return (
    <HtmlInCanvasMotionBlur
      width={width}
      height={height}
      samples={8}
      shutterAngle={180}
    >
      <MovingBox />
    </HtmlInCanvasMotionBlur>
  );
};
```

For live preview, enable HTML-in-canvas in Chrome 149 or later with `chrome://flags/#canvas-draw-element`.  
No configuration for rendering is necessary.

Nest `<HtmlInCanvas>` or `<HtmlInCanvasMotionBlur>` components only when `HtmlInCanvas.isNestingSupported()` returns `true` (Chrome 157.0.8080.0 or newer with HTML-in-canvas enabled).

If HTML-in-canvas is unavailable, see the [motion blur guide](https://www.remotion.dev/docs/motion-blur) for other options. See the [`<HtmlInCanvasMotionBlur>` reference](https://www.remotion.dev/docs/motion-blur/html-in-canvas-motion-blur) for API details.
