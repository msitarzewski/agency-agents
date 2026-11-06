// Minimal Remotion scaffold for the map explainer. In a Remotion project (`bunx create-video@latest`,
// blank template), this is `src/Root.tsx`; `src/index.ts` is just `registerRoot(RemotionRoot)`.
//
// The Composition sets DURATION (the beat) and dimensions. The component reads durationInFrames / width /
// height from useVideoConfig(). The beat must be long enough for the last country's full sequence after
// the river reaches it. See references/map-explainer-architecture.md §2.
// Render with: bunx remotion render src/index.ts MapExplainer out.mp4 --gl=angle --concurrency=1 --timeout=120000

import React from 'react';
import {Composition} from 'remotion';
import {RiverReveal} from './RiverReveal'; // → src/components/RiverReveal.tsx in your project

export const RemotionRoot: React.FC = () => (
	<Composition
		id="MapExplainer"
		component={RiverReveal}
		durationInFrames={12 * 30} // 12 s @ 30 fps — raise if a later country needs more room after the river arrives
		fps={30}
		width={1920}
		height={1080}
	/>
);
