# 3D Flyover — troubleshooting

## The headless dead-end (why we render through Remotion)

Cesium's globe **will not draw in a standalone headless Playwright/Chromium** harness. Verified on
Apple M4 (ANGLE Metal active, WebGL working): the skybox/stars render, but the globe surface produces
**zero draw commands** (`scene.frameState.commandList.length === 0`), `globe.tilesLoaded` never goes
true, and frames come back as the black starfield. No network failures; `sampleTerrainMostDetailed`
succeeds (terrain data is reachable). Dead-ends tried, all failed:

- default render loop, manual `scene.render()`, manual `viewer.render()`, headed mode (context-destroyed).

**What works:** render Cesium **through Remotion** — same headless Chrome, but driven by Remotion's frame
loop with these four non-negotiables:

1. `useDefaultRenderLoop = false` — drive frames by hand.
2. Per frame call **`viewer.render()`**, NOT `scene.render()`. `viewer.render()` does the full frame
   (`initializeFrame` → tile streaming → render); `scene.render()` skips frame-init, so tiles never
   advance and the globe never appears. **This is the single most important line.**
3. `contextOptions: { webgl: { preserveDrawingBuffer: true } }` so Remotion's screenshot captures pixels.
4. Gate init + every frame with `delayRender(…, {timeoutInMilliseconds})` — tile loading can exceed Remotion's
   default; use 60–120 s.

The standalone `flythrough.html` / `render.mjs` / `probe.mjs` from the original spike are kept only as the
record of this dead-end. The canonical render path is the Remotion component
(`../assets/CesiumFlythrough.tsx`).

## Symptom → fix

| Symptom                                                   | Cause                                                                                                         | Fix                                                                                                 |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Frames are black with stars                               | Globe not drawing (headless Playwright, or `scene.render()` used)                                             | Render through Remotion; use `viewer.render()`; `useDefaultRenderLoop=false`.                       |
| Screenshots blank/transparent                             | No `preserveDrawingBuffer`                                                                                    | `contextOptions:{ webgl:{ preserveDrawingBuffer:true } }`.                                          |
| "delayRender timed out"                                   | Cold tiles exceed the default                                                                                 | `delayRender(…, {timeoutInMilliseconds: 120000})` + `--timeout=180000`.                             |
| Globe is a dark/navy sphere                               | Imagery layer didn't attach                                                                                   | `baseLayer:false` then `viewer.imageryLayers.addImageryProvider(...)`.                              |
| High-pitch frame shows a void/starfield above the horizon | No atmosphere                                                                                                 | `viewer.scene.skyAtmosphere.show = true`.                                                           |
| 403 on tiles in headless                                  | Domain-locked MapTiler key                                                                                    | Use an **unrestricted** key.                                                                        |
| Google root tileset returns 403                           | Map Tiles API disabled, billing absent, wrong key, or application restriction blocks local headless rendering | Enable Map Tiles API and billing; restrict the key to that API while allowing the Remotion request. |
| Google scene shows a duplicate/competing surface          | MapTiler or the Cesium globe is still enabled                                                                 | Do not add MapTiler; set `viewer.scene.globe.show=false`.                                           |
| Google mesh remains coarse                                | Screen-space error is too high or the capture starts before refinement                                        | Lower `maximumScreenSpaceError`; settle on `tileset.tilesLoaded`.                                   |
| WebGL unavailable / software renderer                     | Missing GL flag                                                                                               | Render with `--gl=angle`.                                                                           |
| Camera looks at sky / ground, not terrain                 | Pitch sign / convention                                                                                       | Cesium pitch 0 = horizon, negative = down (inverse of MapLibre); `-(90 - PITCH_FROM_NADIR)`.        |
| Aim/turn-probe clamps near the end                        | Path too short                                                                                                | `PATHKM ≥ TRAVEL_KM + 2·LOOK_AHEAD_KM`; raise `WINDOW_KM` in prep.                                  |
| Path feels like straight-then-corner                      | Douglas-Peucker simplification                                                                                | Use resample → moving-average smooth (see architecture §2), not `turf.simplify`.                    |
| Camera bumps left and right instead of swerving           | Sparse route vertices are still being followed as straight segments                                           | Keep `pathSmoothingPasses={3}`; use sparse intentional control points and arc-length movement.      |

## Gotchas checklist

- **`viewer.render()`, never `scene.render()`** per frame. The single biggest trap.
- Cesium loads from **CDN**; set `window.CESIUM_BASE_URL` _before_ injecting the script.
- `preserveDrawingBuffer: true` or screenshots are blank.
- `delayRender` uses `timeoutInMilliseconds`; set it to at least 60,000.
- Terrain: `baseLayer:false`, then add MapTiler imagery.
- Google: no MapTiler, hide the globe, retain `showCreditsOnScreen:true`.
- Always `skyAtmosphere.show = true`.
- Validate the path's heading-delta probe and render one **still** (framing + bank) before the full mp4.
- Cesium pitch/roll conventions are inverted vs MapLibre.
