# Connected compositions

A connected composition lets the user open a scene or element in its own
Studio timeline while editing the implementation used by the parent video.
Use it for a substantial scene, a reusable card, or a group that should move
and be edited together, such as a sticker with its sound or a summary graphic.
A layout container or decorative detail usually belongs inside that group as
plain HTML.

## Create the connection

1. Export the component with `Interactive.create()`. Use `layout: 'absolute-fill'`
   for a scene or `layout: 'none'` for a bounded element.
2. Render that exported component in the parent, with its instance props inline.
   Put timing directly on it, or on the shared `Sequence` or
   `TransitionSeries.Sequence` that governs its layers.
3. Register the exact same exported reference in `<Composition component={...}>`.
   Give the registration a unique literal ID, inline metadata, and representative
   inline `defaultProps`. Registering an inner component or an inline wrapper
   does not connect the instance the user sees.

Follow the complete timeline example
for the component definitions, parent, and registrations.

Each independently editable instance still needs its own JSX node. Reuse a
component for repeated units rather than copying its implementation or generating
all instances from one `.map()` call. Keep editor-owned data at its editable
source: caption arrays belong inline on the caption component, not behind a
prop of a generic shot component.

## Make the component independent of its parent

The parent is not mounted when the standalone composition opens. Load fonts
inside the component or a shared imported module, and keep required typography
there. Supply representative content, background, and alignment in the
registration's defaults. Those defaults do not automatically apply to parent
instances or copy their props.

Match the parent's fps and dimensions unless a difference is intentional.
Preserve the source-time offset as well as the duration when the component's
captions or overlays read original-media frames. The instance's placement in
the parent timeline does not usually belong in its standalone defaults.

## Extract an existing group

For a pre-compose request, move the selected markup into a named component and
register it. If the selection already has a meaningful timing wrapper, keep
that wrapper and its props in place and extract its contents. Preserve trim,
speed, stacking order, inherited styles, and the duration needed by sound tails.
A new component file without its registration does not complete the connection.

## Verify both views

Open the full composition and the standalone composition. Check that the group
looks and sounds the same, that its timeline has useful editing units, and that
double-clicking the parent instance opens the intended composition. For a
refactor, compare representative frames and check cut boundaries, captions,
entrance animations, and audio tails.

Connected compositions provide editing boundaries, not a promise to collapse
all their rows. Studio's compact-series view can expose connected children.
Inspect the full-video timeline as well as the standalone view before claiming
that an extraction reduced clutter. Treat row expansion or unused vertical
space as a layout issue when the markup already expresses the correct groups;
avoid extra wrappers or hidden editable layers solely to force a compact view.
