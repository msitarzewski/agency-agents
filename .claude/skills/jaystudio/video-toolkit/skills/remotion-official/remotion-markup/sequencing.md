---
name: sequencing
description: Sequencing patterns for Remotion - delay, trim, limit duration of items
metadata:
  tags: sequence, series, timing, delay, trim
---

# Choose the timing boundary

Put timing props directly on a built-in interactive component or one made with
`Interactive.create()` when that item should be edited independently. Set audio
timing and volume on `Audio` from `@remotion/media`.

Use a shared `Sequence` when several layers must inherit the same trim, speed,
or start time, when overriding dimensions for descendants, or when the child
does not accept timing props. Choose `layout="none"` if the group should not
add a layout element; otherwise its absolute-fill layout also positions the
contents.

Use `Track` for non-overlapping items with independent positions and
`TransitionSeries` for consecutive items that should shift together when a
duration changes. Keep the series' own sequence boundaries, including when a
child already accepts timing props.

Follow [editable timeline structure](../remotion-interactivity/timeline-structure.md)
for grouping and examples. See [timing props](timing-props.md) for how `from`,
`trimBefore`, duration, speed, and looping combine, and
[editable video timelines](video-editing.md) for synchronized footage and captions.
