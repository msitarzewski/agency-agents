# Cropping

Preferably, the `cropLeft`, `cropRight`, `cropTop` and `cropBottom` props are used to crop content.
It allows for interactively dragging the components and adapting the outlines in the canvas to the crop.

The following components support `crop*` props:

- `<Sequence>` from `remotion`, when `layout="absolute-fill"`
- `<Interactive.*>` HTML and SVG elements from `remotion`
- Custom components made with `Interactive.create()` from `remotion`, using a managed `layout: 'absolute-fill'` root or forwarding `style` to their own visual root
- `<CanvasImage>` from `remotion`
- `<Img>` from `remotion`
- `<AnimatedImage>` from `remotion`
- `<HtmlInCanvas>` from `remotion`
- `<Solid>` from `remotion`
- `<Video>` from `@remotion/media`
- `<Gif>` from `@remotion/gif`
- `<RemotionRiveCanvas>` from `@remotion/rive`

Crop values are ratios between `0` and `1`.
A value of `0` applies no crop on that edge.
A value of `1` is a full crop.
Keep [Interactivity Best Practices](../remotion-interactivity/REFERENCE.md) also for cropping, to keep it editable and keyframable.

```tsx
<CanvasImage
  src={staticFile("photo.png")}
  cropLeft={interpolate(frame, [0, 30], [0, 0.25], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  })}
  cropBottom={0.1}
/>
```

Do not use `clipPath` together with crop props.
