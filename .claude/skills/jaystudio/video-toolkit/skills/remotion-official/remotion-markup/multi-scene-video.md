# Multi-scene videos

Give each substantial scene its own component and connect it when it benefits
from an independent editing timeline. Keep each instance's name, timing, and
props inline in the parent.

Choose the parent structure from the editing behavior:

- For independent scene start times, use a named `Track` with explicit `from`
  and `durationInFrames` on each scene. Its items must not overlap.
- For scenes that should remain adjacent as their durations change, use
  `TransitionSeries`. Keep each scene inside its own
  `TransitionSeries.Sequence`, with duration and source trim on that boundary.
  Add transitions when needed and account for their overlaps in the total
  composition duration.

Follow [editable timeline structure](../remotion-interactivity/timeline-structure.md)
for a complete scene, parent, and registration example. See
[transitions](transitions.md) for transition timing and presentations, and
[connected compositions](connected-compositions.md) for extraction and
verification in the full video.
