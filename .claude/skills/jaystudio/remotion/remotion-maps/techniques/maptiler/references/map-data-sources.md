# Map element data sources

Choose the source independently for every story element. A single map can—and often should—mix
provider vectors with custom geodata.

## Decision rule

Use a MapTiler Planet vector layer when the feature already exists there, its attributes support an
editorially precise filter, and provider geometry is acceptable for the claim. Use custom GeoJSON when
the feature is absent, proposed, historical, disputed, corrected, privately sourced, or needs ordered
geometry for a deterministic draw.

| Requirement                                                                 | MapTiler vector layer | Custom GeoJSON                              |
| --------------------------------------------------------------------------- | --------------------- | ------------------------------------------- |
| Roads, waterways, water, boundaries, land cover, or other standard context  | Prefer                | Use only when provider data is insufficient |
| Basemap-consistent geometry without a duplicate local dataset               | Prefer                | No                                          |
| Proposed, historical, classified, corrected, or production-specific element | No                    | Prefer                                      |
| Fade, colour, width, radius, blur, or fill-opacity animation                | Yes                   | Yes                                         |
| Feature-state highlight when a stable feature ID exists                     | Yes                   | Yes                                         |
| Deterministic source-to-end line draw or perimeter draw                     | Bake first            | Prefer                                      |
| Geometry editing, morphing, clipping, or exact sequencing                   | No                    | Prefer                                      |

Provider alignment is not proof of correctness. Inspect the attributes and geometry against the
editorial source before presenting a provider feature as evidence.

## MapTiler vector mode

MapTiler Planet is a vector tile source. Add it once, then build story layers with a
`source-layer` and an exact attribute filter. Read the current MapTiler Planet schema before choosing
layer names or fields.

Common layer categories include `waterway`, `water`, `transportation`, `boundary`, `landcover`, and
`poi`; availability, fields, and zoom ranges vary by schema version.

```ts
import {addMapTilerVectorElement, setVectorElementPaint} from "./MapTilerVectorElement";

addMapTilerVectorElement(map, process.env.REMOTION_MAPTILER_KEY!, {
  id: "story-river",
  sourceLayer: "waterway",
  type: "line",
  filter: [
    "all",
    ["==", ["get", "class"], "river"],
    ["==", ["coalesce", ["get", "name_en"], ["get", "name"]], "Yarlung Tsangpo"],
  ],
  layout: {"line-cap": "round", "line-join": "round"},
  paint: {
    "line-color": "#E8F7FF",
    "line-width": 3,
    "line-opacity": 0,
  },
});

setVectorElementPaint(map, "story-river", {
  "line-opacity": reveal,
  "line-width": 2 + reveal * 2,
});
```

Animate provider features by changing paint properties from the Remotion frame: opacity, colour,
width, blur, fill opacity, circle radius, or symbol opacity. Use feature state only when the source
provides stable IDs and the selection remains deterministic across tiles.

Do not treat a tiled line as one ordered path. Vector tiles split features at tile boundaries, so a
source-to-mouth or start-to-end draw has no reliable global order. If that motion carries meaning,
extract and verify the complete feature, order it once, save it as GeoJSON, and use the custom mode.

## Custom geodata mode

Use the bundled `../assets/RiverReveal.tsx` and `../scripts/prep-geo.mjs` pattern for custom GeoJSON. This mode owns
the exact geometry and can slice it by distance, calculate entry triggers, draw complete borders, and
produce deterministic sequences.

Custom mode is mandatory when:

- the feature is not in the provider dataset;
- the story uses a proposed route, planned tunnel, historical boundary, disputed interpretation, or
  non-public dataset;
- provider geometry was editorially corrected;
- motion must travel through the geometry in a verified order;
- a complete off-screen boundary matters and a viewport query would silently crop it.

## Hybrid mode

Use provider vectors for ordinary contextual features and custom GeoJSON for the specific claim. For
example: MapTiler waterways and roads as aligned context; a custom proposed tunnel, dam site, disputed
boundary, or verified evacuation area as the highlighted evidence.

Keep provider and custom layers visually distinct when they carry different evidentiary weight. Record
the source and effective date of every custom layer in the production notes.
