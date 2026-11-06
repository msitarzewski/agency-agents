import * as maptilersdk from '@maptiler/sdk';
import * as turf from '@turf/turf';
import React, {useEffect, useRef, useState} from 'react';
import '@maptiler/sdk/dist/maptiler-sdk.css';
import {
	AbsoluteFill,
	Easing,
	continueRender,
	delayRender,
	interpolate,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {CountryLabel} from './CountryLabel';
import countryMeta from './sample-data/country-meta.json';
import flowCoords from './sample-data/yarlung-flow.json';
import {COLORS, COUNTRY, COUNTRY_DARK, FILL_OPACITY} from './tokens';

// Sample route reveal. Replace the imported sample geometry, names, timing, and visual tokens in the
// consuming production. The renderer stays static; approved centre/zoom motion is a CSS plate transform.

maptilersdk.config.apiKey = process.env.REMOTION_MAPTILER_KEY as string;

const line = turf.lineString(flowCoords as [number, number][]);
const lineKm = turf.length(line);

const START = {
	center: [89.6, 27.7] as [number, number],
	zoom: 4.75,
	pitch: 0,
	bearing: 0,
};
const END = {
	center: [90.2, 27.0] as [number, number],
	zoom: 5.05,
	pitch: 0,
	bearing: 0,
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

const ORDER = ['china', 'india', 'bangladesh'] as const;
type Country = (typeof ORDER)[number];
const META = countryMeta as Record<
	Country,
	{stop: number; anchor: [number, number]; border: [number, number][][]}
>;
const countryPolygons = {
	type: 'FeatureCollection' as const,
	features: ORDER.map((country) => ({
		type: 'Feature' as const,
		properties: {country},
		geometry: {
			type: 'MultiPolygon' as const,
			coordinates: META[country].border.map((ring) => [ring]),
		},
	})),
};

// Pre-build each country's border as ordered segments with cumulative lengths (for the multi-segment draw).
const DRAW = Object.fromEntries(
	ORDER.map((c) => {
		const segLines = META[c].border.map((s) => turf.lineString(s));
		const segLen = segLines.map((l) => turf.length(l));
		const cum: number[] = [];
		let acc = 0;
		for (const L of segLen) {
			cum.push(acc);
			acc += L;
		}
		return [c, {segLines, segLen, cum, total: acc}];
	}),
) as Record<
	Country,
	{segLines: any[]; segLen: number[]; cum: number[]; total: number}
>;

// Reveal the portion of the border between fromKm and toKm as a MultiLineString (no joins across gaps).
const sliceBorder = (
	d: (typeof DRAW)[Country],
	fromKm: number,
	toKm: number,
) => {
	const out: number[][][] = [];
	for (let i = 0; i < d.segLines.length; i++) {
		const start = d.cum[i],
			end = start + d.segLen[i];
		const a = Math.max(fromKm, start),
			b = Math.min(toKm, end);
		if (b - a <= 0.0008) continue;
		out.push(
			turf.lineSliceAlong(d.segLines[i], a - start, b - start).geometry
				.coordinates,
		);
	}
	return {
		type: 'Feature' as const,
		properties: {},
		geometry: {type: 'MultiLineString' as const, coordinates: out},
	};
};
const EMPTY = {
	type: 'Feature' as const,
	properties: {},
	geometry: {type: 'MultiLineString' as const, coordinates: [] as number[][][]},
};

// --- Timing (seconds). River draws over [RIVER_START, RIVER_END]; each country triggers when the river
// reaches it (stop · span), then runs border → fill → label. Beat length is derived from these. ---
const RIVER_START = 0.3;
const RIVER_END = 8.0;
const BORDER_S = 2.5;
const FILL_S = 1.0;
const LABEL_S = 0.7;
const trigger = (c: Country) =>
	RIVER_START + META[c].stop * (RIVER_END - RIVER_START);

export const RiverReveal: React.FC = () => {
	const ref = useRef<HTMLDivElement>(null);
	const started = useRef(false);
	const frame = useCurrentFrame();
	const {fps, durationInFrames, width, height} = useVideoConfig();
	const [map, setMap] = useState<any>(null);
	const [labels, setLabels] = useState<
		Record<string, {x: number; y: number; reveal: number}>
	>({});
	const [plate, setPlate] = useState({x: 0, y: 0, scale: 1});
	const [handle] = useState(() => delayRender('maptiler init A'));

	useEffect(() => {
		if (!ref.current || started.current) return;
		started.current = true;
		const m = new maptilersdk.Map({
			container: ref.current,
			style: maptilersdk.MapStyle.BASIC,
			center: END.center,
			zoom: Math.max(START.zoom, END.zoom),
			pitch: END.pitch,
			bearing: END.bearing,
			interactive: false,
			attributionControl: true,
			navigationControl: false,
			geolocateControl: false,
			maptilerLogo: true,
			fadeDuration: 0,
			canvasContextAttributes: {preserveDrawingBuffer: true},
		} as any);

		m.on('load', () => {
			// Strip basemap labels (symbols) AND the inner admin-1 borders ('Other border[ dash]',
			// admin_level 3–10) to cut basemap clutter. Keep country + disputed borders.
			for (const l of m.getStyle().layers as any[])
				if (l.type === 'symbol' || /other border/i.test(l.id))
					m.removeLayer(l.id);

			m.addSource('countries', {type: 'geojson', data: countryPolygons});
			for (const c of ORDER) {
				m.addLayer({
					id: `fill-${c}`,
					type: 'fill',
					source: 'countries',
					filter: ['==', ['get', 'country'], c],
					paint: {'fill-color': COUNTRY[c], 'fill-opacity': 0},
				});
			}
			// Per country: just the border that draws on, settled to a darker shade of the country colour
			// (the electricity now lives on the river, not the borders).
			for (const c of ORDER) {
				m.addSource(`trail-${c}`, {type: 'geojson', data: EMPTY});
				m.addLayer({
					id: `trail-${c}`,
					type: 'line',
					source: `trail-${c}`,
					layout: {'line-cap': 'round', 'line-join': 'round'},
					paint: {
						'line-color': COUNTRY_DARK[c],
						'line-width': 2,
						'line-opacity': 0.95,
					},
				});
			}

			const seed = turf.lineSliceAlong(
				line,
				0,
				Math.max(0.001, lineKm * 0.001),
			);
			m.addSource('river', {type: 'geojson', data: seed});
			m.addSource('river-head', {type: 'geojson', data: seed});
			// Electric water: soft blue glow → icy core → white-hot leading head with its own glow.
			m.addLayer({
				id: 'river-glow',
				type: 'line',
				source: 'river',
				layout: {'line-cap': 'round', 'line-join': 'round'},
				paint: {
					'line-color': '#49C6FF',
					'line-width': 11,
					'line-opacity': 0.32,
					'line-blur': 6,
				},
			});
			m.addLayer({
				id: 'river-line',
				type: 'line',
				source: 'river',
				layout: {'line-cap': 'round', 'line-join': 'round'},
				paint: {'line-color': COLORS.river, 'line-width': 3},
			});
			m.addLayer({
				id: 'river-headglow',
				type: 'line',
				source: 'river-head',
				layout: {'line-cap': 'round', 'line-join': 'round'},
				paint: {
					'line-color': COLORS.riverHeadGlow,
					'line-width': 16,
					'line-opacity': 0,
					'line-blur': 9,
				},
			});
			m.addLayer({
				id: 'river-head',
				type: 'line',
				source: 'river-head',
				layout: {'line-cap': 'round', 'line-join': 'round'},
				paint: {
					'line-color': COLORS.riverHead,
					'line-width': 4.5,
					'line-opacity': 0,
				},
			});

			m.once('idle', () => {
				setMap(m);
				continueRender(handle);
			});
		});
	}, [handle]);

	useEffect(() => {
		if (!map) return;
		const h = delayRender(`frame A ${frame}`);
		const t = frame / fps; // seconds
		const tt = interpolate(frame, [0, durationInFrames - 1], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		});

		// River draw
		const reveal = interpolate(t, [RIVER_START, RIVER_END], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: Easing.bezier(0.645, 0.045, 0.355, 1),
		});
		const riverDrawnKm = lineKm * reveal;
		(map.getSource('river') as any)?.setData(
			turf.lineSliceAlong(line, 0, Math.max(0.001, riverDrawnKm)),
		);
		// Electric draw-head leading the river: white-hot core + glow, fading out once the river completes.
		const riverHeadKm = lineKm * 0.03;
		(map.getSource('river-head') as any)?.setData(
			turf.lineSliceAlong(
				line,
				Math.max(0, riverDrawnKm - riverHeadKm),
				Math.max(0.001, riverDrawnKm),
			),
		);
		let riverHeadFade = 0;
		if (reveal > 0.002 && reveal < 0.999) riverHeadFade = 1;
		else if (reveal >= 0.999)
			riverHeadFade = 1 - clamp01((t - RIVER_END) / 0.5);
		map.setPaintProperty(
			'river-headglow',
			'line-opacity',
			0.85 * riverHeadFade,
		);
		map.setPaintProperty('river-head', 'line-opacity', riverHeadFade);

		const camera = {
			center: [
				lerp(START.center[0], END.center[0], tt),
				lerp(START.center[1], END.center[1], tt),
			] as [number, number],
			zoom: lerp(START.zoom, END.zoom, tt),
		};
		const cameraPoint = map.project(camera.center);
		const plateScale = 2 ** (camera.zoom - Math.max(START.zoom, END.zoom));
		const plateX = width / 2 - cameraPoint.x * plateScale;
		const plateY = height / 2 - cameraPoint.y * plateScale;

		const pos: Record<string, {x: number; y: number; reveal: number}> = {};
		for (const c of ORDER) {
			const d = DRAW[c];
			const lt = t - trigger(c); // local seconds since this country triggered

			// 1) border draws on (constant duration), settling to a darker shade — no electric head
			const bp = interpolate(clamp01(lt / BORDER_S), [0, 1], [0, 1], {
				easing: Easing.bezier(0.645, 0.045, 0.355, 1),
			});
			(map.getSource(`trail-${c}`) as any)?.setData(
				bp <= 0 ? EMPTY : sliceBorder(d, 0, d.total * bp),
			);

			// 2) fill blooms in (overshoot then settle) after the border completes
			const fp = clamp01((lt - BORDER_S) / FILL_S);
			const fo = interpolate(
				fp,
				[0, 0.6, 1],
				[0, FILL_OPACITY * 1.25, FILL_OPACITY],
				{
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
					easing: Easing.bezier(0.3333333333333333, 1, 0.6666666666666666, 1),
				},
			);
			map.setPaintProperty(`fill-${c}`, 'fill-opacity', fp <= 0 ? 0 : fo);

			// 3) label rises in after the fill
			const lp = clamp01((lt - BORDER_S - FILL_S) / LABEL_S);
			const p = map.project(META[c].anchor);
			pos[c] = {
				x: p.x * plateScale + plateX,
				y: p.y * plateScale + plateY,
				reveal: lp,
			};
		}
		setLabels(pos);

		setPlate({x: plateX, y: plateY, scale: plateScale});
		map.once('idle', () => continueRender(h));
		map.triggerRepaint();
	}, [map, frame, fps, durationInFrames, width, height]);

	return (
		<AbsoluteFill style={{backgroundColor: COLORS.bg}}>
			<div
				ref={ref}
				style={{
					width: width * 2,
					height: height * 2,
					position: 'absolute',
					transform: `translate(${plate.x}px, ${plate.y}px) scale(${plate.scale})`,
					transformOrigin: '0 0',
				}}
			/>
			<AbsoluteFill style={{pointerEvents: 'none'}}>
				{ORDER.map((c) =>
					labels[c] ? (
						<CountryLabel
							key={c}
							name={c.toUpperCase()}
							color={COUNTRY[c]}
							reveal={labels[c].reveal}
							x={labels[c].x}
							y={labels[c].y}
						/>
					) : null,
				)}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
