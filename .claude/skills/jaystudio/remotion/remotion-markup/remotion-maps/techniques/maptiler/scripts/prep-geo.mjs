// Geo prep for the map-explainer. Bakes the data the component reads:
//   out/river-flow.json    -> the river draw-on line   (→ copy to your Remotion project's src/geo/)
//   out/country-meta.json  -> per-country { stop, anchor, border }   (→ src/geo/)
//   out/borders.geojson    -> country polygons, each tagged {country}  (→ public/geo/  — loaded via staticFile)
//
// RUN:  node prep-geo.mjs        (needs YOUR geodata — see CONFIG; the source polygons are too large to ship,
//                                 so the skill ships the OUTPUTS in assets/sample-data/ instead.)
//
// RIVER INPUT MUST BE ONE CLEAN LINESTRING, source → mouth (features[0].geometry is a LineString). If your
// OSM river comes as many ways / braided channels, ROUTE it into a single line FIRST — a graph
// shortest-path from source node to mouth node. Do NOT greedily chain by nearest endpoint: it bounces
// between parallel channels. (That routing step is a prerequisite, not part of this script.)

import {readFileSync, writeFileSync, mkdirSync} from 'fs';
import {dirname, resolve} from 'path';
import {fileURLToPath} from 'url';

if (process.argv.includes('--help')) {
	console.log(
		'Configure COUNTRIES, RIVER, BORDER, label bounds, and output paths in this script, then run: bun scripts/prep-geo.mjs',
	);
	process.exit(0);
}

const turf = await import('@turf/turf');

const __dir = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dir, '..');
const geo = resolve(root, '../geodata'); // ADAPT: where your input GeoJSON lives
const read = (p) => JSON.parse(readFileSync(p, 'utf8'));

// ===== CONFIG — edit for your river + countries =====
const COUNTRIES = ['china', 'india', 'bangladesh']; // ORDERED headwaters → mouth; first = source (stop 0)
const RIVER = resolve(geo, 'focus-rivers/yarlung-brahmaputra-full-osm.geojson'); // a single clean source→mouth LineString
const BORDER = (name) => resolve(geo, `project-borders/${name}.geojson`); // one polygon file per country, named <country>.geojson
const FRAME_BBOX = [76, 14, 104, 33.5]; // [W,S,E,N] visible extent — fallback for label anchoring only
const ANCHOR_BBOX = {
	china: [82, 27, 96, 32],
	india: [76, 14, 99, 31],
	bangladesh: [86, 20, 93, 27],
}; // [W,S,E,N] per-country label "story region"
const NUDGE = {china: [0, 0.6], india: [-1.0, 0], bangladesh: [0, -0.6]}; // [lng,lat] label nudge
const RIVER_SIMPLIFY_TOL = 0.006; // degrees — smooths the draw-on (bigger = simpler)
const OUT_RIVER = resolve(root, 'out/river-flow.json');
const OUT_META = resolve(root, 'out/country-meta.json');
const OUT_BORDERS = resolve(root, 'out/borders.geojson');
// =====================================================

const havKm = (a, b) => {
	const R = 6371,
		r = Math.PI / 180;
	const dLat = (b[1] - a[1]) * r,
		dLng = (b[0] - a[0]) * r;
	const h =
		Math.sin(dLat / 2) ** 2 +
		Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLng / 2) ** 2;
	return 2 * R * Math.asin(Math.sqrt(h));
};

// --- River draw-on line: take the clean routed LineString, strip a dangling final hop, simplify so the
// wide-zoom draw-on reads as one smooth thread (no bezier — meander overshoot on a long river). ---
const routed = read(RIVER).features[0].geometry.coordinates;
let end = routed.length;
while (end > 2 && havKm(routed[end - 2], routed[end - 1]) > 15) end--; // drop a final cross-braid jump if present
const flow = turf.simplify(turf.lineString(routed.slice(0, end)), {
	tolerance: RIVER_SIMPLIFY_TOL,
	highQuality: true,
}).geometry.coordinates;

// --- Borders + country fills (one source, filtered per country in the component) ---
const borders = {type: 'FeatureCollection', features: []};
const polys = {};
for (const name of COUNTRIES) {
	const fc = read(BORDER(name));
	polys[name] = fc;
	for (const f of fc.features) {
		f.properties = {...(f.properties || {}), country: name};
		borders.features.push(f);
	}
}

// --- Reveal stops: arc-length fraction of `flow` where the river first ENTERS each country. The first
// country (headwaters) is the source, so its stop is 0; the rest are computed. ---
const flowKm = turf.length(turf.lineString(flow));
const insideCountry = (pt, name) =>
	polys[name].features.some((f) => turf.booleanPointInPolygon(pt, f));
const stops = {};
COUNTRIES.forEach((c, i) => {
	stops[c] = i === 0 ? 0 : 1;
}); // 0 = headwaters; 1 = sentinel until entered
let acc = 0;
for (let i = 0; i < flow.length; i++) {
	if (i > 0) acc += havKm(flow[i - 1], flow[i]);
	const frac = acc / (flowKm || 1);
	const pt = turf.point(flow[i]);
	for (const c of COUNTRIES)
		if (stops[c] === 1 && insideCountry(pt, c)) stops[c] = frac;
}

// --- Per-country meta: anchor = pole of inaccessibility of the visible landmass (centred, away from
// borders/edges) within the country's story region + a NUDGE; border = every exterior ring from the
// complete named source. Never crop a country or bilateral boundary to the viewport. ---
const biggestPoly = (geom) => {
	const rings =
		geom.type === 'MultiPolygon' ? geom.coordinates : [geom.coordinates];
	let best = null,
		bestA = -1;
	for (const c of rings) {
		const p = turf.polygon(c);
		const a = turf.area(p);
		if (a > bestA) {
			bestA = a;
			best = p;
		}
	}
	return best;
};
const largestPolygon = (fc) => {
	let best = null,
		bestA = -1;
	for (const f of fc.features) {
		const p = biggestPoly(f.geometry),
			a = turf.area(p);
		if (a > bestA) {
			bestA = a;
			best = p;
		}
	}
	return best;
};
const completeExteriorSegments = (fc) => {
	const segments = [];
	for (const feature of fc.features) {
		const polygons =
			feature.geometry.type === 'MultiPolygon'
				? feature.geometry.coordinates
				: [feature.geometry.coordinates];
		for (const polygon of polygons)
			if (polygon[0]?.length > 1) segments.push(polygon[0]);
	}
	return segments;
};
const poleOfInaccessibility = (poly) => {
	const bb = turf.bbox(poly),
		boundary = turf.polygonToLine(poly),
		N = 46;
	let best = null,
		bestD = -1;
	for (let i = 0; i <= N; i++)
		for (let j = 0; j <= N; j++) {
			const lng = bb[0] + ((bb[2] - bb[0]) * i) / N,
				lat = bb[1] + ((bb[3] - bb[1]) * j) / N;
			const pt = turf.point([lng, lat]);
			if (!turf.booleanPointInPolygon(pt, poly)) continue;
			const d = turf.pointToLineDistance(pt, boundary);
			if (d > bestD) {
				bestD = d;
				best = [lng, lat];
			}
		}
	return best;
};
const countryMeta = {};
for (const name of COUNTRIES) {
	const poly = largestPolygon(polys[name]);
	const storyRegion = biggestPoly(
		turf.bboxClip(poly, ANCHOR_BBOX[name] || FRAME_BBOX).geometry,
	);
	const pole = poleOfInaccessibility(storyRegion);
	const segs = completeExteriorSegments(polys[name]);
	const nudge = NUDGE[name] || [0, 0];
	countryMeta[name] = {
		stop: stops[name],
		anchor: [pole[0] + nudge[0], pole[1] + nudge[1]],
		border: segs,
	};
}

mkdirSync(dirname(OUT_RIVER), {recursive: true});
writeFileSync(OUT_RIVER, JSON.stringify(flow));
writeFileSync(OUT_META, JSON.stringify(countryMeta));
writeFileSync(OUT_BORDERS, JSON.stringify(borders));
console.log(
	'river:',
	flow.length,
	'pts ·',
	flowKm.toFixed(0),
	'km · entry stops',
	JSON.stringify(stops),
);
for (const n of COUNTRIES) {
	const km = countryMeta[n].border.reduce(
		(s, seg) => s + turf.length(turf.lineString(seg)),
		0,
	);
	console.log(
		`  ${n}: anchor ${countryMeta[n].anchor.map((v) => v.toFixed(2)).join(',')} · border ${km.toFixed(0)} km`,
	);
}
console.log(
	"\nNext: copy out/river-flow.json + out/country-meta.json → your project's src/geo/ ; out/borders.geojson → public/geo/",
);
