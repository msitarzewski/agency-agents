---
name: remotion-create
description: Create a new Remotion video
version: 4.0.540
---

These are instructions for making a new Remotion project and composition.  
If this is not the next task, see [Remotion Best Practices](../SKILL.md)

## Scaffold a project

If a project already exists, skip this.
Ensure Node.js and Git is installed, and the current folder is appropriate for starting a new project.

Inspect the current folder, including hidden files, before choosing where to scaffold.

### Empty folder

If it is empty, or contains only disposable operating-system metadata such as `.DS_Store`, create the project directly in the current folder.
Remove only those disposable metadata files first, since `create-video` rejects non-empty folders.
Do not treat all hidden files as disposable: files such as `.env` and directories such as `.git` are meaningful contents.

Scaffold in existing folder:

```bash
npx create-video@latest --yes --blank --no-tailwind .
npm i
```

### Non-empty folder

If the current folder contains meaningful contents and no project already exists, scaffold into a new subfolder.
Replace `my-video` with a suitable project name.

```bash
npx create-video@latest --yes --blank --no-tailwind my-video
cd my-video
npm i
```

## Open the preview before building the video

As soon as the project can run, open [Remotion Studio](../remotion-studio/REFERENCE.md) in the browser before writing or changing the composition. For a new project, do this immediately after scaffolding and installing dependencies. For an existing project, do it before editing the video. Keep Studio running while you work so the user can see changes as they appear and steer the result.

## Designing a video

Keep the scaffold and add React Markup.
Follow [Remotion React Markup Best Practices](../remotion-markup/REFERENCE.md) and [Video Layout Rules](video-layout.md) for video-first layout and text sizing guidance.

Before writing the root that registers `<Composition>` or `<Still>` elements,
follow [Compositions and stills](../remotion-markup/compositions.md).

## Is this a timeline of clips?

If the video arranges multiple video or audio clips on a timeline, follow
[Video editing](../remotion-markup/video-editing.md) before writing the
timeline. Give every clip that should be edited independently its own authored
JSX node.

## Is this a multi-scene video?

If this is a video with multiple subsequent scenes, follow guidance at [Multi-scene videos](../remotion-markup/multi-scene-video.md).

## Interactivity Best Practices

By structuring the React Markup following [Remotion Interactivity Best Practices](../remotion-interactivity/REFERENCE.md), you allow the user to make edits in the Studio which write back to code.

## TailwindCSS

If Tailwind is requested, see [tailwind.md](tailwind.md) for using TailwindCSS in Remotion.

## Follow-up

The video creation process has finished.
For follow-up prompts, use [Remotion Best Practices](../SKILL.md)
