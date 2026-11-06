---
name: player
description: Embed a Remotion preview in a React app with @remotion/player.
metadata:
  tags: remotion, player, preview, react
---

Use `@remotion/player` when the user wants an interactive preview in React.

```tsx
import {Player} from '@remotion/player';
import {MyVideo} from './remotion/MyVideo';

export const App: React.FC = () => {
  return (
    <Player
      component={MyVideo}
      durationInFrames={120}
      compositionWidth={1920}
      compositionHeight={1080}
      fps={30}
      controls
    />
  );
};
```

If metadata is dynamic, sync the Player props manually or reuse the composition's `calculateMetadata()` logic.
Link https://www.remotion.dev/docs/dynamic-metadata.md#with-the-player.

Full API for the Player: https://www.remotion.dev/docs/player/player.md.

For a SaaS app that also needs output files, combine the Player preview with [framework.md](framework.md) or [rendering.md](rendering.md).
