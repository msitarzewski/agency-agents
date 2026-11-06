# CesiumJS — 3D flyovers in Remotion

Instructions for achieving map animations with "flight-simulator" perspective in Remotion.

## Modes

| Mode        | Data                                                  | Use for                                                |
| ----------- | ----------------------------------------------------- | ------------------------------------------------------ |
| `landscape` | MapTiler `terrain-quantized-mesh-v2` + `satellite-v2` | Mountains, gorges, rivers, coastlines and rural routes |
| `city`      | Google Photorealistic 3D Tiles                        | Cities, architecture and recognizable landmarks        |

Do not use footprint extrusions for city flyovers. They produce crude building blocks rather than
textured architecture.

## Credentials

For `landscape`, set:

```text
REMOTION_MAPTILER_KEY=...
```

Create a MapTiler key at https://cloud.maptiler.com/account/keys/.

For `city`, set:

```text
REMOTION_GOOGLE_MAPS_API_KEY=...
```

Create a billing-enabled Google Map Tiles API key by following
https://developers.google.com/maps/documentation/tile/get-api-key. Enable the **Map Tiles API** and
restrict the key to that API. Ensure its application restriction permits local headless Remotion
requests.

## Build the flight

1. Copy `assets/CesiumFlythrough.tsx`, a path JSON and `assets/example-Root.tsx` into the Remotion
   project, or import the component directly.
2. Supply the camera route as `[longitude, latitude][]`. Use only meaningful control points; do not hand-author dozens of tiny corrections.
3. Leave `pathSmoothingPasses={3}` initially. The component applies repeated Chaikin corner cutting, turning straight-then-corner input into a continuous swerve. Increase to `4` for a softer route or reduce to `2` when the camera must follow a tight corridor.
4. Set absolute camera altitudes for the location. City cameras normally fly lower than landscape
   cameras.
5. Render a middle-frame still before rendering the full video.

```tsx
<CesiumFlythrough
  mode="city"
  path={cameraPath}
  pathSmoothingPasses={3}
  altitudeStart={700}
  altitudeEnd={500}
  lookAheadKm={0.7}
  travelKm={4.5}
/>
```

## Camera behavior

Walk the smoothed curve by arc length for constant ground speed. Aim at a real point farther along
the curve rather than its next vertex. Derive roll from the change in look-ahead bearing so the
camera banks into a turn instead of twitching left and right.

For landscape routes, `scripts/prep-cesium-path.mjs` also clips, resamples, smooths and dampens a
GeoJSON centerline before the component applies its final curve smoothing.


## Mechanics

- Set `viewer.useDefaultRenderLoop = false`.
- Call `viewer.render()`, never `scene.render()`, while settling.
- Use `preserveDrawingBuffer: true`.
- Gate initialization and every frame with `delayRender`.
- Drive camera animation from `useCurrentFrame()`; do not use CSS transitions or browser-timed animation.
- Settle landscapes on `globe.tilesLoaded` and cities on `tileset.tilesLoaded`.
- Keep all provider attribution visible.
- Record the source and effective date of custom or disputed geography.
- Inspect rendered pixels, not only Studio playback, at every required aspect ratio.
- Read `references/3d-flyover-architecture.md` for camera math, `references/3d-data-sources.md` for provider details, and `references/3d-troubleshooting.md` for blank, coarse, unauthorized or timed-out renders.

## Files

- `assets/CesiumFlythrough.tsx` — reusable two-mode component.
- `assets/flight-path.ts` — dependency-free Chaikin route smoothing.
- `assets/example-Root.tsx` — landscape and city compositions.
- `assets/cesium-path.json` — sample landscape route.
- `assets/city-path.json` — sample city route.
- `assets/sample-river.geojson` — sample path-preparation input.
- `scripts/prep-cesium-path.mjs` — dependency-free landscape route preparation.
