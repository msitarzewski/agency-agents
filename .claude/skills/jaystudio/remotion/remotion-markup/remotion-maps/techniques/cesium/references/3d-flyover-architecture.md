# 3D Flyover — architecture reference

Deep detail behind `TECHNIQUE.md`: provider loading, the camera-path pipeline, per-frame camera math, and
the proven terrain values. Both landscape and city modes have been forward-tested through Remotion.

## 1. Provider initialization

Create the Viewer with `baseLayer: false`, UI widgets disabled, and
`contextOptions.webgl.preserveDrawingBuffer: true`. Never hide the credit display.

### Landscape

Add MapTiler `satellite-v2` with `UrlTemplateImageryProvider`, then load
`terrain-quantized-mesh-v2` with `CesiumTerrainProvider.fromUrl({requestVertexNormals: true})`.
MapTiler supplies both datasets; no Cesium ion token is required.

### City

Do not add MapTiler. Hide the globe, then add:

```ts
viewer.scene.globe.show = false;
const tileset = await Cesium.Cesium3DTileset.fromUrl(
  `https://tile.googleapis.com/v1/3dtiles/root.json?key=${GOOGLE_KEY}`,
  {showCreditsOnScreen: true, maximumScreenSpaceError: 4},
);
viewer.scene.primitives.add(tileset);
```

Lower `maximumScreenSpaceError` improves refinement at substantial download/render cost. Start at
`4` for a hero landmark and `6–8` for wider urban shots. Enforce the Google 30-second promotional
video ceiling in the component.

Load Cesium from the CDN after setting `window.CESIUM_BASE_URL`; the tested version is `1.143`.

## 2. The camera path — structure & generation

Four properties matter, in order:

1. **Continuous curvature** — the camera must flow through curves, never "fly straight, snap to a new
   heading, fly straight." The component applies three passes of **Chaikin corner cutting** to every
   supplied path. Each pass replaces a segment with quarter and three-quarter points, rounding a
   corner into a curve. Three passes are the default; four is softer, two is tighter.
2. **Constant ground speed** — precompute cumulative distance along the rounded curve and interpolate
   by arc length. Do not animate by source-point index; unequal source spacing creates speed bumps.
3. **Minimized amplitude** — for detailed landscape centerlines, dampen the prepared path toward its
   straight start→end chord by a fixed fraction `DAMP` (0 = dead straight, 1 = full river). This is
   the single swerve-amplitude knob.
4. **Enough length** — `PATHKM ≥ TRAVEL_KM + 2·LOOK_AHEAD_KM` so the look-ahead aim never clamps.

`../scripts/prep-cesium-path.mjs` does: clip a window of the source centerline → resample to even
arc-length spacing (0.1 km) → moving-average smooth (±2.8 km window, 2 passes) → dampen toward the chord
(`DAMP=0.45`). Validate with the heading-delta probe it prints — deltas should be small and change
_gradually_ (water-wars: `3,0,-1,-3,-4,1,7,9,5,-5,-12,-7,…`). Big jumps = corners = bad.

The component then applies Chaikin smoothing to this prepared route, or directly to a short
hand-authored city route. Keep city control points sparse and intentional; smoothing cannot rescue a
zig-zagging route that crosses the subject repeatedly.

**Source data:** OSM via Overpass (~0.3 km vertex spacing) — Natural Earth is too coarse for inner
gorges. overpass-api.de is often busy → mirror `overpass.kumi.systems`.

## 3. Camera animation per frame (position, heading, pitch, bank)

Walk the path by **arc length** (precompute cumulative distances once). Every frame:

- **Position** = the point at `dCam` km along the path, altitude `lerp(ALT_START, ALT_END, prog)`.
- **Heading** = bearing from the camera point to a **real point `LOOK_AHEAD_KM` further along the same
  path**. A far aim averages wiggle → smooth heading; on a curved path it leads into the bend, so the
  heading turns gently with the path. (A local-tangent aim spins the camera at every kink — don't.)
- **Pitch** = constant. We keep a MapLibre-style param `PITCH_FROM_NADIR` (90 = horizon), then convert:
  **Cesium pitch = `-(90 - PITCH_FROM_NADIR)`** (Cesium: 0 = horizon, -90 = straight down). 76° → -14°.
- **Bank (roll)** = lean _into_ the turn — the helicopter tell. Measure turn rate as the bearing change
  between `aim` and a point `2·LOOK_AHEAD_KM` ahead; `roll = clamp(dH · BANK_GAIN, ±MAX_BANK)`. Because
  the path is smooth, `dH` changes gradually → the bank eases in and out, never jerks.

```ts
const setCamera = (C, viewer, prog) => {
  const dCam = Math.min(TRAVEL_KM, PATHKM - LOOK_AHEAD_KM * 2) * prog;
  const cam  = alongPath(dCam);                    // arc-length point
  const aim  = alongPath(dCam + LOOK_AHEAD_KM);     // heading target (real point on the path)
  const aim2 = alongPath(dCam + LOOK_AHEAD_KM * 2); // turn-rate probe → bank
  const heading = bearing(cam, aim);
  let dH = bearing(aim, aim2) - heading; while (dH > Math.PI) dH -= 2*Math.PI; while (dH < -Math.PI) dH += 2*Math.PI;
  viewer.camera.setView({
    destination: C.Cartesian3.fromDegrees(cam[0], cam[1], lerp(ALT_START, ALT_END, prog)),
    orientation: { heading, pitch: C.Math.toRadians(-(90 - PITCH_FROM_NADIR)), roll: clamp(dH * BANK_GAIN, -MAX_BANK, MAX_BANK) },
  });
};
```

> **Cesium vs MapLibre conventions (gotcha):** Cesium heading is radians, 0 = north, clockwise. Pitch
> 0 = horizon, negative = down (MapLibre is the inverse). Roll positive = bank right; tune the sign by eye.

## 4. The feel — proven water-wars values

| Param                    | Value                  | Meaning                                                                              |
| ------------------------ | ---------------------- | ------------------------------------------------------------------------------------ |
| `TRAVEL_KM`              | 13                     | How far the camera travels. **Speed = `TRAVEL_KM / durationSeconds`.**               |
| duration                 | 24 s (720 f @30)       | 13 km / 24 s ≈ **0.54 km/s** — a slow, peaceful glide. 8 s felt "extremely rushed".  |
| `ALT_START → ALT_END`    | 4600 → 4300 m ASL      | Absolute (terrain-independent). Inside the corridor walls → fly _through_, not over. |
| `LOOK_AHEAD_KM`          | 1.5                    | Heading smoothness vs responsiveness.                                                |
| `PITCH_FROM_NADIR`       | 76°                    | Stare-ahead down the corridor (90 = level). → Cesium -14°.                           |
| `MAX_BANK` / `BANK_GAIN` | 0.13 rad (~7.5°) / 0.6 | Helicopter lean into turns.                                                          |
| `verticalExaggeration`   | 1.1                    | Subtle terrain drama.                                                                |
| `DAMP` (prep)            | 0.45                   | Swerve amount: higher = weavier, lower = straighter.                                 |

**A slow camera renders fast.** At 0.54 km/s the camera moves ~18 m/frame, so tiles stay cached and each
`settle()` returns almost immediately; the 720-frame render completed in one pass (no chunk-rendering).

## 5. The complete component

The full, runnable component is `../assets/CesiumFlythrough.tsx` — read it directly. Its shape:

- `loadCesium()` — inject `CESIUM_BASE_URL` + the CDN `Cesium.js`, resolve when loaded.
- init effect — build the Viewer (§1), `setCamera(…, 0)`, `await settle(viewer)`, `continueRender`.
- `settle(viewer)` — loop `viewer.render()` until `globe.tilesLoaded` for landscapes or
  `tileset.tilesLoaded` for cities is stable for ~8 ticks (cap ~600).
- per-frame effect — `delayRender({timeoutInMilliseconds: 60000})` → `setCamera(prog)` → `settle()` → `continueRender`.

## 6. Render

```bash
bunx remotion still   src/index.ts <Comp> out.png --frame=N --gl=angle --timeout=180000   # validate framing/bank first
bunx remotion render  src/index.ts <Comp> out.mp4  --gl=angle --concurrency=1 --timeout=180000
```

`--gl=angle` is mandatory. Use `--concurrency=1`; `settle()` already serializes tile loading.
