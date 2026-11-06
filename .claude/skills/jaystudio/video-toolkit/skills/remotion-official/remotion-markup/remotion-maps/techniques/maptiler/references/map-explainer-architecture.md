# Map Explainer — architecture reference

Deep detail behind `TECHNIQUE.md`: the timing model, the river reveal + electric head, the per-country
sequence, and label projection. The supplied values are examples, not a production style system.
The custom-geometry example is `../assets/RiverReveal.tsx` +
`../assets/CountryLabel.tsx` +
`../assets/tokens.ts`. Provider-vector setup is in
`../assets/MapTilerVectorElement.ts`; choose between
the two modes with `data-sources.md`.

## 1. The render harness (per frame)

Init the MapTiler map once (ref guard). On `load`: strip clutter (see `geo-prep.md`), add sources/layers,
wait for `once('idle') → continueRender`. Per frame:

```
delayRender → setData/setPaintProperty → map.once('idle', continueRender) → triggerRepaint
```

`preserveDrawingBuffer:true` so Remotion's screenshot captures the canvas. Render `--gl=angle`.
For an animated camera, read `render-stability.md`: the MapTiler renderer remains static and a CSS plate
transform supplies the camera choreography.

## 2. Timing model — time-based; beat length derived from the sequences

Everything keys off **seconds** (`t = frame / fps`), not reveal-units. The river draws over a window;
each country **triggers when the river reaches it** and runs a fixed sequence. The beat is exactly as
long as the sequences need.

```ts
const RIVER_START = 0.3, RIVER_END = 8.0;            // river draws over this window
const BORDER_S = 2.5, FILL_S = 1.0, LABEL_S = 0.7;   // per-country sequence (constant durations)
const trigger = (c) => RIVER_START + META[c].stop * (RIVER_END - RIVER_START);  // river-arrival time
// beat length = max over c of (trigger(c) + BORDER_S + FILL_S + LABEL_S) + tail
const reveal = interpolate(t, [RIVER_START, RIVER_END], [0,1], { ...clamp, easing: Easing.bezier(0.645, 0.045, 0.355, 1) });
```

**Constant durations matter:** drive the border draw by _time since trigger_, not a slice of the reveal —
otherwise complex or long borders flash by in a fraction of a second.

## 3. Provider-vector animation

MapTiler Planet elements can be animated directly in place. Filter an exact `source-layer` feature,
initialize its paint in the hidden or neutral state, then update paint properties from the Remotion frame.
This works for line, fill, circle, and symbol layers without copying provider geometry into the project.

Do not assume tiled geometry has a global order. Provider features are split at tile boundaries: opacity,
colour, width, blur, radius, fill, and feature-state changes are reliable; semantic start-to-end line
draws are not. Bake ordered GeoJSON when the direction of the draw carries meaning.

## 4. Custom line animation — reveal + electric draw-head

The "electricity" is a **white-hot head** leading the draw — the last few % of the drawn line in its own
bright + glow layers, faded out once the river completes.

```ts
const riverDrawnKm = lineKm * reveal;
map.getSource("river").setData(turf.lineSliceAlong(line, 0, Math.max(0.001, riverDrawnKm)));
const headKm = lineKm * 0.03;
map.getSource("river-head").setData(turf.lineSliceAlong(line, Math.max(0, riverDrawnKm - headKm), Math.max(0.001, riverDrawnKm)));
let headFade = 0;
if (reveal > 0.002 && reveal < 0.999) headFade = 1;
else if (reveal >= 0.999) headFade = 1 - clamp01((t - RIVER_END) / 0.5);  // fade out at the mouth
map.setPaintProperty("river-headglow", "line-opacity", 0.85 * headFade);
map.setPaintProperty("river-head", "line-opacity", headFade);
```

Layers, bottom→top: `river-glow` (electric blue `#49C6FF`, w11, op0.32, blur6) → `river-line`
(icy core `#E8F7FF`, w3) → `river-headglow` (`rgba(120,225,255,.95)`, w16, blur9) → `river-head`
(white `#FFFFFF`, w4.5). **No dark casing** — the bright icy core reads over every fill on its own.

## 5. Country animation — border draws → fill blooms → label rises

Triggered by river arrival, each country runs three sequential phases. The border is a **darker shade**
of the country colour (the electricity is on the river, not here).

```ts
const lt = t - trigger(c);                                   // local seconds since trigger
// 1) complete source border draws on over a constant BORDER_S, multi-segment-safe
const bp = interpolate(clamp01(lt / BORDER_S), [0,1], [0,1], { easing: Easing.bezier(0.645, 0.045, 0.355, 1) });
map.getSource(`trail-${c}`).setData(sliceBorder(DRAW[c], 0, DRAW[c].total * bp));   // COUNTRY_DARK line
// 2) fill blooms in (opacity overshoots, then settles) after the border completes
const fp = clamp01((lt - BORDER_S) / FILL_S);
const fo = interpolate(fp, [0, 0.6, 1], [0, FILL_OPACITY * 1.25, FILL_OPACITY], { ...clamp, easing: Easing.bezier(0.3333333333333333, 1, 0.6666666666666666, 1) });
map.setPaintProperty(`fill-${c}`, "fill-opacity", fp <= 0 ? 0 : fo);
// 3) label rises in after the fill
const lp = clamp01((lt - BORDER_S - FILL_S) / LABEL_S);
```

`sliceBorder(d, fromKm, toKm)` reveals a portion of a complete (possibly multi-segment) border as a
MultiLineString, slicing each segment by cumulative length — no joins across gaps and no viewport crop:

```ts
const sliceBorder = (d, fromKm, toKm) => {
  const out = [];
  for (let i = 0; i < d.segLines.length; i++) {
    const start = d.cum[i], end = start + d.segLen[i];
    const a = Math.max(fromKm, start), b = Math.min(toKm, end);
    if (b - a <= 0.0008) continue;
    out.push(turf.lineSliceAlong(d.segLines[i], a - start, b - start).geometry.coordinates);
  }
  return { type:"Feature", properties:{}, geometry:{ type:"MultiLineString", coordinates: out } };
};
```

Choose fill, border, and river colours in the production's local token file. The bundled token values are
examples only; do not carry a source project's palette into another production.

## 6. Labels — HTML overlay, projected each frame

Labels are React, not map symbols (full typography control). `CountryLabel` is an example accent-rule,
rise-and-fade treatment; select the typeface and final values in the production.
Positioned by projecting the anchor to screen pixels **every frame**, stored in state:

```ts
const p = map.project(META[c].anchor);   // lngLat → screen px (respects the live camera)
pos[c] = { x: p.x, y: p.y, reveal: lp };
setLabels(pos);                          // re-render the overlay; effect deps exclude `labels`
```

`CountryLabel` shows the mechanics: uppercase region name, short accent divider, rise/fade entrance,
and `pointerEvents:none`. Select font, weight, size, spacing, contrast, and colour from the production's
own type and palette system.

## 7. Camera — fixed map plate for any movement

Read `render-stability.md`. Do not use per-frame `map.jumpTo()` for a moving 2D shot; it can shimmer in
headless renders even on satellite imagery. Interpolate the intended camera for the CSS plate transform,
while keeping the MapTiler renderer static.
