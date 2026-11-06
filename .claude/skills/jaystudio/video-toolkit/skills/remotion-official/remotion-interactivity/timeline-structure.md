# Editable timeline structure

Choose what the user should be able to move, trim, style, duplicate, or delete
together before adding timeline items. A scene, a captioned shot, a summary
card, or a sticker with its entrance sound can each be one editable unit.
Use plain HTML for the layout and decoration inside that unit. Add an
`Interactive` element when it needs independent selection or controls.

Write each independently editable instance as its own JSX node, with a literal
name and inline timing and appearance props. Reuse the component implementation
for repeated cards or stickers, but keep their instances separate. Use loops for
output intentionally controlled as one template, such as particles or chart
bars, rather than independently editable clips.

## Choose how items share time

| Editing behavior                                                 | Structure                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------- |
| Items have independent start times and do not overlap            | A named `Track`, with timing on each item                           |
| Consecutive clips should stay adjacent when one changes duration | `TransitionSeries`, with timing on each `TransitionSeries.Sequence` |
| Several layers must move, trim, or change speed together         | One timed component or `Sequence` containing those layers           |

A track is useful for scenes, music segments, cutaways, stickers, or sound
effects. Group non-overlapping siblings by role instead of giving every item
its own row. Items that remain visible together need separate tracks or a
component that contains their shared layout. Staggered entrances do not make
overlapping cards suitable for one track.

Put timing directly on components that accept it. Avoid a `Sequence` around a
single timing-capable child just to name or register it. Keep wrappers that
provide shared timing, dimensions, or `TransitionSeries` behavior. Use
`layout="none"` on a `Sequence` when it should not introduce a layout element.

For captioned footage and overlays spanning cuts, read
[editable video timelines](../remotion-markup/video-editing.md).

## Give substantial groups their own timelines

Create a connected composition when a scene or reusable element benefits from
being edited on its own. Export it with `Interactive.create()` and register the
same reference with `Composition`.

- Use `layout: 'absolute-fill'` for a scene. Return a fragment and put its
  background and alignment styles on the instance; the managed root applies them.
- Use `layout: 'none'` for a bounded element. Forward `style` to its plain root.
  The component already owns a timeline item, so the root does not need another
  `Interactive.Div` for the same controls.

Connection enables drill-down and shared implementation. It does not guarantee
fewer rows in the parent: Studio can display connected children inside a series.
Choose useful editing boundaries, then inspect the actual parent timeline.
Do not add wrapper components or hide editable content just to alter row counts.

## Complete example

The title is one editable element. Its scene has a connected timeline, while
independently timed scenes and music segments each share a named track.

```tsx title="Title.tsx"
import type React from 'react';
import {Interactive} from 'remotion';

const TitleInner = ({
  children,
  style,
}: {
  readonly children: React.ReactNode;
  readonly style: React.CSSProperties;
}) => <h1 style={{margin: 0, ...style}}>{children}</h1>;

export const Title = Interactive.create({
  Component: TitleInner,
  layout: 'none',
  schema: {
    ...Interactive.textSchema,
    ...Interactive.childrenSchema,
  },
});
```

```tsx title="Chapter.tsx"
import {Interactive} from 'remotion';
import {Title} from './Title';

const ChapterInner = ({title}: {readonly title: string}) => (
  <>
    <Title
      name="Chapter title"
      style={{fontFamily: 'Arial, sans-serif', fontSize: 96, color: 'white'}}
    >
      {title}
    </Title>
  </>
);

export const Chapter = Interactive.create({
  Component: ChapterInner,
  layout: 'absolute-fill',
  schema: {
    ...Interactive.backgroundSchema,
    title: {type: 'string', default: '', description: 'Title'},
  },
});
```

```tsx title="MyVideo.tsx"
import {Audio} from '@remotion/media';
import {staticFile, Track, useVideoConfig} from 'remotion';
import {Chapter} from './Chapter';

export const MyVideo = () => {
  const {fps} = useVideoConfig();
  return (
    <>
      <Track name="Chapters">
        <Chapter
          name="Opening"
          durationInFrames={3 * fps}
          title="Introduction"
          style={{
            backgroundColor: '#111111',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        />
        <Chapter
          name="Feature"
          from={3 * fps}
          durationInFrames={4 * fps}
          title="New features"
          style={{
            backgroundColor: '#243b53',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        />
      </Track>
      <Track name="Music">
        <Audio
          name="Opening music"
          src={staticFile('music.mp3')}
          durationInFrames={2 * fps}
        />
        <Audio
          name="Closing music"
          src={staticFile('music.mp3')}
          from={4 * fps}
          trimBefore={10 * fps}
          durationInFrames={3 * fps}
        />
      </Track>
    </>
  );
};
```

```tsx title="Root.tsx"
import {Composition, Folder} from 'remotion';
import {Chapter} from './Chapter';
import {MyVideo} from './MyVideo';
import {Title} from './Title';

export const RemotionRoot = () => (
  <>
    <Composition
      id="MyVideo"
      component={MyVideo}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={210}
    />
    <Folder name="Scenes">
      <Composition
        id="Chapter"
        component={Chapter}
        width={1920}
        height={1080}
        fps={30}
        durationInFrames={90}
        defaultProps={{
          title: 'Introduction',
          style: {
            backgroundColor: '#111111',
            justifyContent: 'center',
            alignItems: 'center',
          },
        }}
      />
    </Folder>
    <Folder name="Elements">
      <Composition
        id="Title"
        component={Title}
        width={1920}
        height={1080}
        fps={30}
        durationInFrames={90}
        defaultProps={{
          children: 'Introduction',
          style: {
            fontFamily: 'Arial, sans-serif',
            fontSize: 96,
            color: 'white',
          },
        }}
      />
    </Folder>
  </>
);
```

Keep metadata and defaults inline on each registration. See
[connected compositions](../remotion-markup/connected-compositions.md) for
extracting existing groups and checking both the parent and standalone views.
