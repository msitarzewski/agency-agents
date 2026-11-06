## Delaying, trimming

In the component that renders these items, get `const {fps} = useVideoConfig()`.
Use this `fps` for seconds-to-frames expressions on the JSX node, rather than
a fixed FPS constant.

The following timing props are supported by built-in components (`<AbsoluteFill>`, `<Interactive.*>`, `<Img>`, `<AnimatedImage>`, `<CanvasImage>`, `<HtmlInCanvas>`, `<Solid>`, `<Sequence>`, `<Track>` from `remotion`, `<Video>` and `<Audio>` from `@remotion/media`, `<Gif>`, and more).
Custom components made with `Interactive.create()` accept them too, see Prefer interactive components with their own timelines.

### `from`

When the item starts appearing in the timeline.
Its children start at frame `0` when it appears.

```tsx
<Img from={1 * fps} {/* ... */}/>
<Video from={1 * fps} {/* ... */}/>
<Interactive.Div from={1 * fps} {/* ... */}/>
<LowerThird from={1 * fps} {/* ... */}/>
```

### `trimBefore`

Sets the first frame of the item's own timeline:

```tsx
// Trim away first 2 seconds of footage
<Video trimBefore={2 * fps} {/* ... */} />

// `useCurrentFrame()` of the children starts at `10 * fps`
<Interactive.Div trimBefore={10 * fps} {/* ... */} />
```

### `durationInFrames`

How many frames of the item's own timeline are shown, starting at `trimBefore`.
Use it to end media early instead of cutting the file:

```tsx
// Play the footage from second 2 to second 5
<Video trimBefore={2 * fps} durationInFrames={3 * fps} {/* ... */} />
<Img durationInFrames={20 * fps} {/* ... */}/>
<LowerThird durationInFrames={5 * fps} {/* ... */}/>
```

### `playbackRate`

Changes the speed of the item.
Children calling `useCurrentFrame()` advance `playbackRate` frames per frame of the parent.
The item occupies `durationInFrames / playbackRate` frames in its parent timeline.

```tsx
// 2x speed
<Video playbackRate={2} {/* ... */} />
<LowerThird playbackRate={0.5} durationInFrames={2 * fps} {/* ... */} />
```

### `loop`

Repeats the range selected by `trimBefore` and `durationInFrames` until the parent ends.
`<Video>`, `<Audio>`, `<Gif>` and `<AnimatedImage>` may omit `durationInFrames`; the media's own duration after `trimBefore` then defines the loop range.
Other items need `durationInFrames` to define the loop range:

```tsx
<Video loop {/* ... */} />
<Interactive.Div durationInFrames={2 * fps} loop {/* ... */} />
```

Put timing and volume directly on `<Audio>`.

`<Img>`, `<CanvasImage>`, `<Solid>` and shapes do not support `loop` because their output does not change over time.

### Order of operations

1. `from` positions the item in its parent timeline.
2. `trimBefore` sets the first frame of the item's own timeline.
3. `durationInFrames` selects the range of the item's own timeline.
4. `playbackRate` stretches or compresses the selected range.
5. `loop` repeats the selected range until the parent ends.

Children calling `useCurrentFrame()` get `trimBefore + (frame - from) * playbackRate`.

See [Timing and trimming](https://www.remotion.dev/docs/timing) for more details.

### Fallback

If a component does not support these props, wrap it in `<Sequence>` from `remotion`, which has them.

- `layout="absolute-fill"` makes the Sequence behave like AbsoluteFill
- `layout="none"` is "headless" mode, no wrapper element is used.
