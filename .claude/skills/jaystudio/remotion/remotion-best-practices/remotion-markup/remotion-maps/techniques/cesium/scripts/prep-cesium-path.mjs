// Camera-path generator for the Cesium flythrough. Turns a river/route centerline GeoJSON into a LONG,
// CONTINUOUSLY-curving camera path so the camera banks through smooth flowing curves (no
// straight-then-corner). Method: clip → resample to even spacing → moving-average smooth (inherently
// continuous curvature) → dampen lateral deviation toward the straight chord (dials swerve amplitude).
// No Douglas-Peucker (that concentrates curvature at sparse control points → corners).
//
// RUN (out of the box, against the shipped sample):
//   node prep-cesium-path.mjs
//     → reads  assets/sample-river.geojson   (override: node prep-cesium-path.mjs <input.geojson> <output.json>)
//     → writes assets/cesium-path.json        (then import that JSON in CesiumFlythrough.tsx, or copy it
//                                               into your Remotion project's src/geo/ and adjust the import)
//
// ADAPT for a new location: change START (a point ON your centerline where the corridor opens),
// WINDOW_KM, and DAMP/SMOOTH below. Input must be a single LineString feature (features[0].geometry).

import {readFileSync, writeFileSync, mkdirSync} from 'fs';
import {dirname, resolve} from 'path';
import {fileURLToPath} from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const IN = process.argv[2] || resolve(__dir, '../assets/sample-river.geojson');
const OUT = process.argv[3] || resolve(__dir, '../assets/cesium-path.json');
const havKm = (a, b) => {
	const R = 6371,
		r = Math.PI / 180,
		dLat = (b[1] - a[1]) * r,
		dLng = (b[0] - a[0]) * r;
	const h =
		Math.sin(dLat / 2) ** 2 +
		Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLng / 2) ** 2;
	return 2 * R * Math.asin(Math.sqrt(h));
};

const gorge = JSON.parse(readFileSync(IN, 'utf8')).features[0].geometry
	.coordinates;

// ADAPT: clip ~24 km of river from the reach where the flythrough opens. START must be a point ON the
// centerline (the script snaps to the nearest vertex). The sample's opening is the Yarlung gorge:
const START = [94.968, 29.757];
let s0 = 0,
	best = Infinity;
gorge.forEach((p, i) => {
	const d = havKm(p, START);
	if (d < best) {
		best = d;
		s0 = i;
	}
});
const WINDOW_KM = 30; // clip to ~end of gorge data; smoothing+dampening shrink it to the usable corridor
const clip = [];
for (let i = s0, acc = 0; i < gorge.length; i++) {
	if (i > s0) acc += havKm(gorge[i - 1], gorge[i]);
	if (acc > WINDOW_KM) break;
	clip.push(gorge[i]);
}

// Resample to even arc-length spacing so curvature is distributed evenly along the path.
const STEP_KM = 0.1;
const resample = (coords) => {
	const out = [coords[0].slice()];
	let carry = 0,
		from = coords[0];
	for (let i = 1; i < coords.length; i++) {
		let segLen = havKm(from, coords[i]);
		while (carry + segLen >= STEP_KM) {
			const t = (STEP_KM - carry) / segLen;
			const np = [
				from[0] + (coords[i][0] - from[0]) * t,
				from[1] + (coords[i][1] - from[1]) * t,
			];
			out.push(np);
			from = np;
			segLen = havKm(from, coords[i]);
			carry = 0;
		}
		carry += segLen;
		from = coords[i];
	}
	return out;
};

// Moving-average smoothing — inherently continuous (no kinks). Window in points; repeat for extra glass.
const smoothMA = (coords, w, passes) => {
	let c = coords;
	for (let p = 0; p < passes; p++) {
		c = c.map((_, i) => {
			let sx = 0,
				sy = 0,
				n = 0;
			for (
				let j = Math.max(0, i - w);
				j <= Math.min(c.length - 1, i + w);
				j++
			) {
				sx += c[j][0];
				sy += c[j][1];
				n++;
			}
			return [sx / n, sy / n];
		});
	}
	return c;
};

const SMOOTH_W = 28; // ±2.8 km window — turns meanders into smooth flowing curves
const SMOOTH_PASSES = 2;
const DAMP = 0.45; // keep 45% of the (already-smooth) deviation → gentle, continuous swerve

const even = resample(clip);
const sm = smoothMA(even, SMOOTH_W, SMOOTH_PASSES);

const lat0 = (sm[0][1] * Math.PI) / 180;
const kx = 111.32 * Math.cos(lat0),
	ky = 110.57;
const toXY = (p) => [(p[0] - sm[0][0]) * kx, (p[1] - sm[0][1]) * ky];
const toLL = (xy) => [sm[0][0] + xy[0] / kx, sm[0][1] + xy[1] / ky];
const A = toXY(sm[0]),
	B = toXY(sm[sm.length - 1]);
const AB = [B[0] - A[0], B[1] - A[1]],
	len2 = AB[0] ** 2 + AB[1] ** 2;
const path = sm.map((p) => {
	const P = toXY(p);
	const t = ((P[0] - A[0]) * AB[0] + (P[1] - A[1]) * AB[1]) / len2;
	const proj = [A[0] + t * AB[0], A[1] + t * AB[1]];
	return toLL([
		proj[0] + (P[0] - proj[0]) * DAMP,
		proj[1] + (P[1] - proj[1]) * DAMP,
	]);
});

mkdirSync(dirname(OUT), {recursive: true});
writeFileSync(OUT, JSON.stringify(path));

let len = 0;
for (let i = 1; i < path.length; i++) len += havKm(path[i - 1], path[i]);
console.log(
	`cesium-path: clip ${clip.length} → resample ${even.length} → smooth → ${path.length} pts · ${len.toFixed(1)} km`,
);
const bear = (a, b) => {
	const r = Math.PI / 180;
	const y = Math.sin((b[0] - a[0]) * r) * Math.cos(b[1] * r);
	const x =
		Math.cos(a[1] * r) * Math.sin(b[1] * r) -
		Math.sin(a[1] * r) * Math.cos(b[1] * r) * Math.cos((b[0] - a[0]) * r);
	return (Math.atan2(y, x) * 180) / Math.PI;
};
// heading sampled every ~1.5 km — should change gradually & continuously (no big jumps = no corners)
const stepPts = Math.round(1.5 / STEP_KM);
let prev = null,
	hs = [];
for (let i = 0; i + stepPts < path.length; i += stepPts) {
	const h = bear(path[i], path[i + stepPts]);
	if (prev !== null) {
		let d = h - prev;
		while (d > 180) d -= 360;
		while (d < -180) d += 360;
		hs.push(d.toFixed(0));
	}
	prev = h;
}
console.log(`  heading deltas every 1.5km (deg): ${hs.join(', ')}`);
