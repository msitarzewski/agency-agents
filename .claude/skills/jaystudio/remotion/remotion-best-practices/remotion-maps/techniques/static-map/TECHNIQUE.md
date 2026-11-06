---
name: remotion-maps-static
description: Create a deterministic static locator map in Remotion when neither the camera nor geographic data animates.
---

# Static map

Use a static image when the map only provides location context. This is the smallest, fastest, and
most deterministic map technique.

## Build

1. Export or request a map image at the composition's final aspect ratio and at least its rendered
   pixel dimensions.
2. Store the image in the Remotion project's `public/` directory.
3. Render it with `CanvasImage` and `staticFile()`.
4. Add labels or markers as ordinary Remotion elements if they remain fixed.

```tsx
import React from 'react';
import {AbsoluteFill, CanvasImage, staticFile} from 'remotion';

export const StaticMap: React.FC = () => {
	return (
	  <>
  		<CanvasImage
  			src={staticFile('locator-map.png')}
  			style={{width: '100%', height: '100%', objectFit: 'cover'}}
  		/>
		</>
	);
};
```

## Overlays and Interactivity

Follow [Remotion Interactivity](../../../remotion-interactivity/REFERENCE.md) best practices and [Remotion Markup Best practices](../../../remotion-markup/REFERENCE.md) for elements.
