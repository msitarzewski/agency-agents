// Surface an existing MapTiler Planet feature without maintaining duplicate GeoJSON.
// Paint animation is deterministic; geometry slicing is not. For a source-to-end line draw,
// bake the selected feature to ordered GeoJSON and use RiverReveal.tsx instead.

type VectorLayerType = 'fill' | 'line' | 'circle' | 'symbol';

export type MapTilerVectorElement = {
	id: string;
	sourceLayer: string;
	type: VectorLayerType;
	filter?: unknown[];
	minzoom?: number;
	maxzoom?: number;
	layout?: Record<string, unknown>;
	paint: Record<string, unknown>;
};

const SOURCE_ID = 'maptiler-planet';

export const addMapTilerVectorElement = (
	map: any,
	apiKey: string,
	element: MapTilerVectorElement,
	beforeId?: string,
) => {
	if (!map.getSource(SOURCE_ID)) {
		map.addSource(SOURCE_ID, {
			type: 'vector',
			url: `https://api.maptiler.com/tiles/v3/tiles.json?key=${apiKey}`,
		});
	}

	if (map.getLayer(element.id)) return;

	map.addLayer(
		{
			id: element.id,
			type: element.type,
			source: SOURCE_ID,
			'source-layer': element.sourceLayer,
			...(element.filter ? {filter: element.filter} : {}),
			...(element.minzoom === undefined ? {} : {minzoom: element.minzoom}),
			...(element.maxzoom === undefined ? {} : {maxzoom: element.maxzoom}),
			...(element.layout ? {layout: element.layout} : {}),
			paint: element.paint,
		},
		beforeId,
	);
};

export const setVectorElementPaint = (
	map: any,
	layerId: string,
	paint: Record<string, unknown>,
) => {
	for (const [property, value] of Object.entries(paint)) {
		map.setPaintProperty(layerId, property, value);
	}
};

// Example:
//
// addMapTilerVectorElement(map, process.env.REMOTION_MAPTILER_KEY!, {
//   id: "story-river",
//   sourceLayer: "waterway",
//   type: "line",
//   filter: [
//     "all",
//     ["==", ["get", "class"], "river"],
//     ["==", ["coalesce", ["get", "name_en"], ["get", "name"]], "Yarlung Tsangpo"],
//   ],
//   layout: {"line-cap": "round", "line-join": "round"},
//   paint: {"line-color": "#E8F7FF", "line-width": 3, "line-opacity": 0},
// });
//
// Per Remotion frame:
// setVectorElementPaint(map, "story-river", {
//   "line-opacity": reveal,
//   "line-width": 2 + reveal * 2,
// });
