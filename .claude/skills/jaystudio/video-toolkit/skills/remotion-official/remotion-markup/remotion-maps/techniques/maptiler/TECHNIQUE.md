# MapTiler maps in Remotion

MapTiler is a good solution for map animations where geographics features should be drawn as annotations on top of the map: Country borders, rivers, labels for POIs.

## MapTiler SDK (`@maptiler/sdk`)

Draw the basemap plus MapTiler Planet vector layers and custom GeoJSON into a WebGL canvas. Default styled-vector starting point: `MapStyle.BASIC`; satellite is an equally valid choice.

## Remotion

Imperatively update `setData`/`setPaintProperty`.

Use `jumpTo` only for a static shot, or a fixed map plate for any pan/zoom.
Gate with [`delayRender`](https://www.remotion.dev/docs/delay-render.md) until `map.once('idle')`.

Use `preserveDrawingBuffer:true`.

Render labels as positioned [`<Interactive.Div>`](https://www.remotion.dev/docs/interactive.md) elements.

Env `REMOTION_MAPTILER_KEY` (unrestricted). Init the map once (ref guard); update imperatively per frame.

When constructing MapLibre/MapTiler layer objects, omit optional properties that are absent.  
In particular, use `...(layer.filter ? {filter: layer.filter} : {})`; do not pass `filter: undefined`. An undefined filter can suppress the layer while separately created halo or border layers continue rendering, producing missing country fills and dark marker halos with no coloured cores.

Drive animation from `useCurrentFrame()` rather than CSS transitions or browser timers.  

## Choose the source for each map element

Do not begin by manufacturing GeoJSON. First check whether MapTiler Planet already exposes the element as filtered vector data.

### MapTiler vector

Use it when the feature exists in a provider `source-layer`, its attributes support an exact filter, and provider geometry is editorially acceptable.

### Hybrid

Use it when ordinary geographic context can come from MapTiler while the claim depends on custom
evidence.

Animate each layer according to its source and meaning.

MapTiler vector features remain split across tiles. Do not use them for a semantic start-to-end line draw; extract, verify, order, and bake that element to GeoJSON first. Read **`references/map-data-sources.md`** and reuse **`assets/MapTilerVectorElement.ts`** for provider-layer setup and per-frame paint updates.

## Motion stability

**Do not call `map.jumpTo()` on every Remotion frame when the camera moves.** In headless capture it can make both MapTiler hillshade **and satellite imagery** shimmer/jitter, even when the source tiles load correctly. This is renderer resampling, not a data, network, or label problem.

For the implementation, read **`references/render-stability.md`** before building or debugging any moving map. It contains the fixed-map-plate recipe, diagnostics, and render checks.

- Use the live MapTiler camera only for a static shot.
- Keep pitch and bearing constant for a fixed plate. This technique does not implement a genuine changing 3D camera.
- Verify the moving preview and a short rendered MP4 before approving a beat. If any basemap detail wavers, switch to the fixed-plate pattern; do not try to solve it with tile retries or camera easing.

## Drawing rivers

Use `turf.lineSliceAlong(line, 0, lineKm*reveal)` to draw rivers.

## Source selection

Use MapTiler vector layers for suitable provider features and custom GeoJSON for story-specific or ordered geometry. If the beat needs country-entry triggers or a progressive line draw, run `scripts/prep-geo.mjs` to bake `country-meta.json`, `borders.geojson`, and the ordered line. Details → `references/map-data-sources.md` and `references/map-geo-prep.md`.

## Keep it minmal

Strip clutter on `load`: remove `symbol` layers (place labels) and `/other border/i` (admin-1 inner borders); hide the logo via CSS. Keep country + disputed borders.

## Files

Use as reference:

- `assets/RiverReveal.tsx` — the main component.
- `assets/MapTilerVectorElement.ts` — filtered MapTiler Planet elements.
- `assets/CountryLabel.tsx` — reusable example label.
- `assets/tokens.ts` — example palette and durations.
- `assets/example-Root.tsx` — minimal composition scaffold.
- `assets/sample-data/` — example route and generated country metadata.
- `scripts/prep-geo.mjs` — geo pipeline.
- `references/map-explainer-architecture.md` — timing model and implementation.
- `references/map-data-sources.md` — provider vector versus custom GeoJSON selection.
- `references/map-geo-prep.md` — basemap stripping and geo preparation.
- `references/render-stability.md` — camera motion and stable headless renders.
