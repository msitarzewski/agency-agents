---
name: maps-mapbox
description: Make deterministic Remotion 2D map animations with Mapbox GL JS and Turf. Use when the user chooses Mapbox for animated routes, map markers, labels, camera movement, or Mapbox styles.
metadata:
  tags: map, map animation, mapbox, turf, geojson, route animation
---

Use Mapbox GL JS for rendering maps in Remotion when the user wants Mapbox styles or higher-fidelity map visuals and has a Mapbox access token. Use Turf for geospatial operations such as great-circle routes, distances, slicing lines, and positions along routes.

Use this technique only when the user has a Mapbox access token and wants Mapbox styles or data.

## Core rules

- Prefer `@turf/turf` for geospatial work. Do not hand-roll distance, great-circle, route slicing, or coordinate interpolation unless the user explicitly needs a custom non-geodesic effect.
- Use GeoJSON sources and Mapbox layers for lines, markers, and labels. Avoid DOM `Marker` elements unless the user specifically asks for HTML markers.
- Keep the live map camera static by default. Before moving it on every frame, read [moving-map stability](references/render-stability.md). Prefer a fixed map plate for satellite imagery, hillshade, or a modest 2D reframe.
- Use a live per-frame camera only after rendering a short MP4 and checking for shimmer. This 2D technique does not provide genuine terrain, pitch, bearing, or banking.
- Disable non-deterministic map behavior: `interactive: false`, `fadeDuration: 0`.
- Drive animation from `useCurrentFrame()`; do not use CSS transitions or browser-timed animation.
- Use `delayRender()` / `continueRender()` around map loading and per-frame map updates.
- Set `preserveDrawingBuffer: true` and render WebGL with `bunx remotion ... --gl=angle`.
- Before continuing the initial render, add sources/layers, apply the frame-0 camera with `jumpTo()` or `setFreeCameraOptions()`, then wait for `idle`.
- Do not add a `mapInstance.remove()` cleanup function; it can interfere with Remotion's render lifecycle.
- Use Mapbox style URLs such as `mapbox://styles/mapbox/standard` or a user-provided custom style.
- Do not install `@types/mapbox-gl`; Mapbox GL JS ships its own types.
- Keep required provider attribution visible and verify current provider terms before rendering.
- Record the source and effective date of custom or disputed geography.
- Inspect rendered pixels, not only Studio playback, at every required aspect ratio.

Coordinates in Mapbox, Turf, and GeoJSON are `[longitude, latitude]`.

```ts
const zurich: [number, number] = [8.5417, 47.3769];
const newYork: [number, number] = [-74.006, 40.7128];
```

## Prerequisites

Install Mapbox GL JS and Turf with the project's package manager.

```bash
npm i mapbox-gl @turf/turf
```

```bash
bun i mapbox-gl @turf/turf
```

```bash
yarn add mapbox-gl @turf/turf
```

```bash
pnpm i mapbox-gl @turf/turf
```

Import the Mapbox CSS once in the component or an app-level stylesheet:

```ts
import 'mapbox-gl/dist/mapbox-gl.css';
```

Mapbox requires a public access token. Prefer passing it as an input prop or reading it from an environment variable that is available to the bundled Remotion code.

```ts
const mapboxAccessToken = process.env.REMOTION_MAPBOX_TOKEN;

if (!mapboxAccessToken) {
	throw new Error('Set REMOTION_MAPBOX_TOKEN to render Mapbox maps.');
}
```

## Basic map example

```tsx
import {useEffect, useRef, useState} from 'react';
import {useDelayRender, useVideoConfig} from 'remotion';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const zurich: [number, number] = [8.5417, 47.3769];

const mapboxAccessToken = process.env.REMOTION_MAPBOX_TOKEN;

if (!mapboxAccessToken) {
	throw new Error('Set REMOTION_MAPBOX_TOKEN to render Mapbox maps.');
}

export const MyComposition = () => {
	const containerRef = useRef<HTMLDivElement>(null);
	const {delayRender, continueRender} = useDelayRender();
	const {width, height} = useVideoConfig();
	const [loadingHandle] = useState(() => delayRender('Loading Mapbox map'));

	useEffect(() => {
		if (!containerRef.current) {
			return;
		}

		const mapInstance = new mapboxgl.Map({
			accessToken: mapboxAccessToken,
			container: containerRef.current,
			style: 'mapbox://styles/mapbox/standard',
			center: zurich,
			zoom: 7,
			interactive: false,
			attributionControl: false,
			fadeDuration: 0,
			canvasContextAttributes: {
				preserveDrawingBuffer: true,
			},
		});

		mapInstance.on('load', () => {
			mapInstance.jumpTo({center: zurich, zoom: 7});
			mapInstance.once('idle', () => {
				continueRender(loadingHandle);
			});
		});
	}, [continueRender, loadingHandle]);

	return (
		<>
			<div ref={containerRef} style={{width, height, position: 'absolute'}} />
		</>
	);
};
```

Animated examples should keep the loaded map in React state and skip per-frame updates until that state is set.

## Animated flight route example

This example shows the recommended pattern for route animations:

- Turf creates the route and markers.
- Turf slices the route for line reveal animation.
- Mapbox renders the route with GeoJSON sources and layers.
- The camera uses `jumpTo()` with animated center, zoom, bearing, and pitch.
- Frame 0 is prepared before `continueRender()`.

```tsx
import * as turf from '@turf/turf';
import {useEffect, useRef, useState} from 'react';
import {
	AbsoluteFill,
	Easing,
	interpolate,
	useCurrentFrame,
	useDelayRender,
	useVideoConfig,
} from 'remotion';
import mapboxgl, {type GeoJSONSource, type Map} from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const zurich: [number, number] = [8.5417, 47.3769];
const newYork: [number, number] = [-74.006, 40.7128];

const mapboxAccessToken = process.env.REMOTION_MAPBOX_TOKEN;

if (!mapboxAccessToken) {
	throw new Error('Set REMOTION_MAPBOX_TOKEN to render Mapbox maps.');
}

const greatCircleLine = (from: [number, number], to: [number, number]) => {
	const route = turf.greatCircle(from, to, {npoints: 100});

	if (route.geometry.type === 'LineString') {
		return turf.lineString(route.geometry.coordinates);
	}

	// Great-circle routes crossing the antimeridian can become MultiLineString.
	// Keep the example valid by choosing the longest segment.
	const longestSegment = route.geometry.coordinates.reduce((longest, segment) => {
		return segment.length > longest.length ? segment : longest;
	});

	return turf.lineString(longestSegment);
};

const targetRoute = greatCircleLine(zurich, newYork);
const targetRouteDistance = turf.length(targetRoute);

const cityMarkers = turf.featureCollection([
	turf.point(zurich, {name: 'Zurich'}),
	turf.point(newYork, {name: 'New York'}),
]);

const clampProgress = (progress: number) => Math.min(1, Math.max(0, progress));

const distanceAlong = (totalDistance: number, progress: number) => {
	// Keep the route non-empty at progress 0; Turf can error on zero-length slices.
	return Math.max(0.001, totalDistance * clampProgress(progress));
};

const getPartialTargetRoute = (progress: number) => {
	return turf.lineSliceAlong(
		targetRoute,
		0,
		distanceAlong(targetRouteDistance, progress),
	);
};

const getCameraOptions = (progress: number) => {
	const target = turf.along(
		targetRoute,
		distanceAlong(targetRouteDistance, progress),
	).geometry.coordinates as [number, number];

	return {
		center: target,
		zoom: interpolate(progress, [0, 0.5, 1], [7, 2.4, 8], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: Easing.bezier(0.645, 0.045, 0.355, 1),
		}),
		bearing: interpolate(progress, [0, 1], [-20, 35], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		}),
		pitch: interpolate(progress, [0, 0.25, 0.75, 1], [25, 55, 55, 30], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: Easing.bezier(0.645, 0.045, 0.355, 1),
		}),
	};
};

export const MyComposition = () => {
	const containerRef = useRef<HTMLDivElement>(null);
	const frame = useCurrentFrame();
	const {delayRender, continueRender} = useDelayRender();
	const {durationInFrames, height, width} = useVideoConfig();
	const [map, setMap] = useState<Map | null>(null);
	const [loadingHandle] = useState(() => delayRender('Loading Mapbox map'));

	useEffect(() => {
		if (!containerRef.current) {
			return;
		}

		const mapInstance = new mapboxgl.Map({
			accessToken: mapboxAccessToken,
			container: containerRef.current,
			style: 'mapbox://styles/mapbox/standard',
			center: zurich,
			zoom: 7,
			interactive: false,
			attributionControl: false,
			fadeDuration: 0,
			canvasContextAttributes: {
				preserveDrawingBuffer: true,
			},
		});

		mapInstance.on('load', () => {
			mapInstance.addSource('trace', {
				type: 'geojson',
				data: getPartialTargetRoute(0),
			});

			mapInstance.addLayer({
				id: 'trace-line',
				type: 'line',
				source: 'trace',
				layout: {
					'line-cap': 'round',
					'line-join': 'round',
				},
				paint: {
					'line-color': '#111111',
					'line-width': 7,
				},
			});

			mapInstance.addSource('city-markers', {
				type: 'geojson',
				data: cityMarkers,
			});

			mapInstance.addLayer({
				id: 'city-marker-dots',
				type: 'circle',
				source: 'city-markers',
				paint: {
					'circle-color': '#f03b20',
					'circle-radius': 12,
					'circle-stroke-color': '#ffffff',
					'circle-stroke-width': 4,
				},
			});

			mapInstance.addLayer({
				id: 'city-marker-labels',
				type: 'symbol',
				source: 'city-markers',
				layout: {
					'text-allow-overlap': true,
					'text-anchor': 'top',
					'text-field': ['get', 'name'],
					'text-offset': [0, 0.9],
					'text-size': 28,
				},
				paint: {
					'text-color': '#111111',
					'text-halo-color': '#ffffff',
					'text-halo-width': 3,
				},
			});

			mapInstance.jumpTo(getCameraOptions(0));
			mapInstance.once('idle', () => {
				setMap(mapInstance);
				continueRender(loadingHandle);
			});
		});
	}, [continueRender, loadingHandle]);

	useEffect(() => {
		if (!map) {
			return;
		}

		const handle = delayRender('Rendering Mapbox frame');
		const timelineProgress = interpolate(frame, [0, durationInFrames - 1], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		});
		const travelProgress = interpolate(timelineProgress, [0.2, 0.82], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: Easing.bezier(0.645, 0.045, 0.355, 1),
		});
		const trace = map.getSource('trace') as GeoJSONSource | undefined;

		trace?.setData(getPartialTargetRoute(travelProgress));
		map.jumpTo(getCameraOptions(travelProgress));

		map.once('idle', () => continueRender(handle));
		// Force an idle event even if the camera parameters are unchanged from the previous frame.
		map.triggerRepaint();
	}, [continueRender, delayRender, durationInFrames, frame, map]);

	return (
		<AbsoluteFill style={{backgroundColor: '#e8eef3'}}>
			<div ref={containerRef} style={{height, position: 'absolute', width}} />
		</AbsoluteFill>
	);
};
```

## Camera guidance

For a validated live-camera route animation, animate `center`, `zoom`, `bearing`, and `pitch` with `jumpTo()`:

```ts
map.jumpTo({
	center,
	zoom,
	bearing,
	pitch,
});
```

Keep route progress and camera progress separate if the camera needs to lead, lag, zoom out, or zoom back in. For cinematic 3D camera moves, load the 3D flyover branch from the parent skill.

## Lines

Use GeoJSON sources for lines. Unless the user asks, do not add glow effects or extra decorative points.

For geodesic flight routes, use Turf:

```ts
const line = greatCircleLine(start, end);
const distance = turf.length(line);
const partialLine = turf.lineSliceAlong(
	line,
	0,
	// Keep the route non-empty at progress 0.
	Math.max(0.001, distance * progress),
);
```

For a visually straight line on the map, use a simple GeoJSON `LineString` between the two points instead of `greatCircle()`.

## Markers and labels

Use map-native GeoJSON layers for markers and labels:

```tsx
mapInstance.addSource('markers', {
	type: 'geojson',
	data: turf.featureCollection([
		turf.point([-118.2437, 34.0522], {name: 'Los Angeles'}),
	]),
});

mapInstance.addLayer({
	id: 'marker-dots',
	type: 'circle',
	source: 'markers',
	paint: {
		'circle-color': '#f03b20',
		'circle-radius': 12,
		'circle-stroke-color': '#ffffff',
		'circle-stroke-width': 4,
	},
});

mapInstance.addLayer({
	id: 'marker-labels',
	type: 'symbol',
	source: 'markers',
	layout: {
		'text-allow-overlap': true,
		'text-anchor': 'top',
		'text-field': ['get', 'name'],
		'text-offset': [0, 0.9],
		'text-size': 28,
	},
	paint: {
		'text-color': '#111111',
		'text-halo-color': '#ffffff',
		'text-halo-width': 3,
	},
});
```

Make marker sizes and label font sizes large enough for the composition resolution.

## Styles

Default to Mapbox Standard:

```ts
style: 'mapbox://styles/mapbox/standard'
```

If the user requests another style, use any valid Mapbox style URL.

## Rendering

For WebGL map renders, prefer single concurrency and ANGLE:

```bash
bunx remotion render [composition-id] out/video.mp4 --gl=angle --concurrency=1
```

Use the equivalent package runner for the project. In npm projects, use `npx`; in Bun projects, use `bunx`.
