# Moving Map Render Stability

Read this reference before building a moving 2D MapTiler scene or diagnosing a wavering Remotion render.

## Symptom and cause

If basemap detail shimmers or jitters during a pan/zoom, the likely cause is per-frame `map.jumpTo()`.
Headless MapTiler capture can resample both vector hillshade and satellite imagery differently frame to
frame. Tile retries, easing changes, and label changes do not solve that renderer effect.

## Required pattern: fixed map plate

For any 2D pan/zoom:

1. Render the MapTiler canvas once at the largest required zoom in an oversized container. Size it from the camera route and keep each dimension below the browser's reliable WebGL render-buffer limit (commonly 4096 px). Do **not** blindly use 3×: a 1920×1080 composition becomes 5760 px wide and Chromium may silently downsample it, causing visible pixelation during the CSS zoom.
2. Keep the map's camera static.
3. For each frame, calculate the approved target centre/zoom, then move the canvas with CSS `translate` + `scale`.
4. Apply the same transform to every projected HTML overlay.
5. Continue to animate GeoJSON data and paint properties imperatively; only the renderer camera is frozen.

Keep pitch and bearing constant. Use a 3D engine such as Cesium for genuine changing pitch/bearing or a terrain flythrough.

```ts
const baseZoom = Math.max(start.zoom, end.zoom);
const map = new maptilersdk.Map({
  container,
  style,
  center: end.center,
  zoom: baseZoom,
  pitch: end.pitch ?? 0,
  bearing: end.bearing ?? 0,
  interactive: false,
  fadeDuration: 0,
  canvasContextAttributes: {preserveDrawingBuffer: true},
});

// Per Remotion frame. `camera` is the approved centre/zoom interpolation.
const projected = map.project(camera.center);
const scale = 2 ** (camera.zoom - baseZoom);
const plate = {
  transform: `translate(${width / 2 - projected.x * scale}px, ${height / 2 - projected.y * scale}px) scale(${scale})`,
  transformOrigin: "0 0",
};

// Convert label projection with exactly the same plate transform.
const labelX = labelPoint.x * scale + width / 2 - projected.x * scale;
const labelY = labelPoint.y * scale + height / 2 - projected.y * scale;
```

### Plate sizing and sharpness

- Render at the maximum zoom reached by **any** camera waypoint, including intermediate or hold cameras. The CSS scale should never exceed `1`; otherwise the plate is being enlarged.
- Centre the frozen map on the midpoint of the camera route's geographic extent, not automatically on the final camera. This minimizes required overscan.
- Keep the largest canvas dimension at or below 4096 px unless the actual render environment has been tested with a larger `MAX_RENDERBUFFER_SIZE`.
- For 1920×1080, a 3840×2160 plate is a safe default. For 1080×1920, use approximately 2700×3840 when the route needs extra horizontal pan room.
- If the route cannot fit within that plate at the required zoom, split the shot into two fixed plates with a deliberate editorial transition. Do not trade sharpness for one enormous canvas.
- Distinguish failure modes: repeating shimmer means the live renderer is moving; steadily soft tiles during a CSS push means the fixed plate is underspecified, internally downsampled, or being scaled above `1`.

## Verification

- Render a short MP4, not only a Studio preview.
- Inspect static terrain texture and satellite detail while the camera moves.
- If any underlying map detail wavers, use the fixed map plate. Do not approve it as a minor preview artefact.
- Render WebGL with `--gl=angle`, `preserveDrawingBuffer:true`, and conservative concurrency (`1`) while validating.
