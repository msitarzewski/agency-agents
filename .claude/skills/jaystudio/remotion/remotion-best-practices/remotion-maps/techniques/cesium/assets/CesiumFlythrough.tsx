import React, {useEffect, useMemo, useRef, useState} from 'react';
import {
	AbsoluteFill,
	cancelRender,
	continueRender,
	delayRender,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import terrainPath from './cesium-path.json';
import {smoothFlightPath, type LngLat} from './flight-path';

export type FlyoverMode = 'landscape' | 'city';
export type {LngLat} from './flight-path';

export type CesiumFlythroughProps = {
	mode?: FlyoverMode;
	path?: LngLat[];
	pathSmoothingPasses?: number;
	altitudeStart?: number;
	altitudeEnd?: number;
	lookAheadKm?: number;
	travelKm?: number;
	pitchFromNadir?: number;
	verticalExaggeration?: number;
	maximumScreenSpaceError?: number;
};

const MAPTILER_KEY = process.env.REMOTION_MAPTILER_KEY;
const GOOGLE_MAPS_API_KEY = process.env.REMOTION_GOOGLE_MAPS_API_KEY;
const CESIUM_VER = '1.143';
const CDN = `https://cesium.com/downloads/cesiumjs/releases/${CESIUM_VER}/Build/Cesium/`;
const R = 6371;
const MAX_BANK = 0.13;
const BANK_GAIN = 0.6;

const havKm = (a: number[], b: number[]) => {
	const r = Math.PI / 180;
	const dLat = (b[1] - a[1]) * r;
	const dLng = (b[0] - a[0]) * r;
	const h =
		Math.sin(dLat / 2) ** 2 +
		Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLng / 2) ** 2;
	return 2 * R * Math.asin(Math.sqrt(h));
};

const makePathWalker = (path: LngLat[]) => {
	if (path.length < 2)
		throw new Error('Flyover path needs at least two points');
	const cumulative = [0];
	for (let i = 1; i < path.length; i++) {
		cumulative.push(cumulative[i - 1] + havKm(path[i - 1], path[i]));
	}
	const lengthKm = cumulative[cumulative.length - 1];
	const along = (km: number): LngLat => {
		const d = Math.max(0, Math.min(lengthKm, km));
		let i = 1;
		while (i < cumulative.length && cumulative[i] < d) i++;
		if (i >= cumulative.length) return path[path.length - 1];
		const segmentLength = cumulative[i] - cumulative[i - 1] || 1;
		const t = (d - cumulative[i - 1]) / segmentLength;
		return [
			path[i - 1][0] + (path[i][0] - path[i - 1][0]) * t,
			path[i - 1][1] + (path[i][1] - path[i - 1][1]) * t,
		];
	};
	return {along, lengthKm};
};

const bearing = (a: number[], b: number[]) => {
	const r = Math.PI / 180;
	const y = Math.sin((b[0] - a[0]) * r) * Math.cos(b[1] * r);
	const x =
		Math.cos(a[1] * r) * Math.sin(b[1] * r) -
		Math.sin(a[1] * r) * Math.cos(b[1] * r) * Math.cos((b[0] - a[0]) * r);
	return Math.atan2(y, x);
};

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const clamp = (v: number, lo: number, hi: number) =>
	Math.max(lo, Math.min(hi, v));

const loadCesium = () =>
	new Promise<any>((resolve, reject) => {
		if ((window as any).Cesium) return resolve((window as any).Cesium);
		(window as any).CESIUM_BASE_URL = CDN;
		const css = document.createElement('link');
		css.rel = 'stylesheet';
		css.href = `${CDN}Widgets/widgets.css`;
		document.head.appendChild(css);
		const script = document.createElement('script');
		script.src = `${CDN}Cesium.js`;
		script.onload = () => resolve((window as any).Cesium);
		script.onerror = () =>
			reject(new Error(`Failed to load CesiumJS ${CESIUM_VER}`));
		document.head.appendChild(script);
	});

export const CesiumFlythrough: React.FC<CesiumFlythroughProps> = ({
	mode = 'landscape',
	path = terrainPath as LngLat[],
	pathSmoothingPasses = 3,
	altitudeStart = 4600,
	altitudeEnd = 4300,
	lookAheadKm = 1.5,
	travelKm = 13,
	pitchFromNadir = 76,
	verticalExaggeration = 1.1,
	maximumScreenSpaceError = 8,
}) => {
	const containerRef = useRef<HTMLDivElement>(null);
	const started = useRef(false);
	const viewerRef = useRef<any>(null);
	const tilesetRef = useRef<any>(null);
	const frame = useCurrentFrame();
	const {durationInFrames, fps, width, height} = useVideoConfig();
	const [ready, setReady] = useState(false);
	const [handle] = useState(() =>
		delayRender(`cesium init: ${mode}`, {timeoutInMilliseconds: 120000}),
	);
	const walker = useMemo(
		() => makePathWalker(smoothFlightPath(path, pathSmoothingPasses)),
		[path, pathSmoothingPasses],
	);

	const setCamera = (C: any, viewer: any, progress: number) => {
		const maxTravel = Math.max(0, walker.lengthKm - lookAheadKm * 2);
		const cameraDistance = Math.min(travelKm, maxTravel) * progress;
		const camera = walker.along(cameraDistance);
		const aim = walker.along(cameraDistance + lookAheadKm);
		const aim2 = walker.along(cameraDistance + lookAheadKm * 2);
		const heading = bearing(camera, aim);
		let headingDelta = bearing(aim, aim2) - heading;
		while (headingDelta > Math.PI) headingDelta -= 2 * Math.PI;
		while (headingDelta < -Math.PI) headingDelta += 2 * Math.PI;
		viewer.camera.setView({
			destination: C.Cartesian3.fromDegrees(
				camera[0],
				camera[1],
				lerp(altitudeStart, altitudeEnd, progress),
			),
			orientation: {
				heading,
				pitch: C.Math.toRadians(-(90 - pitchFromNadir)),
				roll: clamp(headingDelta * BANK_GAIN, -MAX_BANK, MAX_BANK),
			},
		});
	};

	const tilesAreLoaded = (viewer: any) => {
		if (mode === 'landscape') return viewer.scene.globe.tilesLoaded;
		return Boolean(tilesetRef.current?.tilesLoaded);
	};

	const settle = (viewer: any) =>
		new Promise<void>((resolve) => {
			let stable = 0;
			let ticks = 0;
			const tick = () => {
				viewer.render();
				ticks++;
				stable = tilesAreLoaded(viewer) ? stable + 1 : 0;
				if (stable > 8 || ticks > 600) {
					viewer.render();
					resolve();
				} else {
					setTimeout(tick, 8);
				}
			};
			tick();
		});

	useEffect(() => {
		if (started.current) return;
		started.current = true;
		(async () => {
			if (mode === 'landscape' && !MAPTILER_KEY) {
				throw new Error(
					'Set REMOTION_MAPTILER_KEY. Create a key at https://cloud.maptiler.com/account/keys/',
				);
			}
			if (mode === 'city' && !GOOGLE_MAPS_API_KEY) {
				throw new Error(
					'Set REMOTION_GOOGLE_MAPS_API_KEY. Create a Map Tiles API key at https://developers.google.com/maps/documentation/tile/get-api-key',
				);
			}
			if (mode === 'city' && durationInFrames / fps > 30) {
				throw new Error(
					'Google Photorealistic 3D Tiles compositions must not exceed 30 seconds',
				);
			}

			const C = await loadCesium();
			const viewer = new C.Viewer(containerRef.current, {
				baseLayer: false,
				baseLayerPicker: false,
				geocoder: false,
				homeButton: false,
				sceneModePicker: false,
				navigationHelpButton: false,
				animation: false,
				timeline: false,
				fullscreenButton: false,
				infoBox: false,
				selectionIndicator: false,
				contextOptions: {webgl: {preserveDrawingBuffer: true}},
			});
			if (mode === 'landscape') {
				viewer.imageryLayers.addImageryProvider(
					new C.UrlTemplateImageryProvider({
						url: `https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=${MAPTILER_KEY}`,
						maximumLevel: 20,
					}),
				);
				viewer.terrainProvider = await C.CesiumTerrainProvider.fromUrl(
					`https://api.maptiler.com/tiles/terrain-quantized-mesh-v2/?key=${MAPTILER_KEY}`,
					{requestVertexNormals: true},
				);
				viewer.creditDisplay.addStaticCredit(
					new C.Credit(
						'<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a>',
						true,
					),
				);
			}
			if (mode === 'city') {
				viewer.scene.globe.show = false;
				const tileset = await C.Cesium3DTileset.fromUrl(
					`https://tile.googleapis.com/v1/3dtiles/root.json?key=${GOOGLE_MAPS_API_KEY}`,
					{
						showCreditsOnScreen: true,
						maximumScreenSpaceError,
					},
				);
				viewer.scene.primitives.add(tileset);
				tilesetRef.current = tileset;
			}

			viewer.useDefaultRenderLoop = false;
			viewer.scene.skyAtmosphere.show = true;
			viewer.scene.fog.enabled = true;
			viewer.scene.globe.enableLighting = false;
			viewer.scene.verticalExaggeration = verticalExaggeration;
			(window as any).__CESIUM_FLYOVER__ = {C, mode};
			viewerRef.current = viewer;
			setCamera(C, viewer, 0);
			await settle(viewer);
			setReady(true);
			continueRender(handle);
		})().catch((error) => cancelRender(error));
	}, [durationInFrames, fps, handle, mode]);

	useEffect(() => {
		if (!ready) return;
		const frameHandle = delayRender(`cesium ${mode} frame ${frame}`, {
			timeoutInMilliseconds: 60000,
		});
		const C = (window as any).__CESIUM_FLYOVER__.C;
		const viewer = viewerRef.current;
		const progress = durationInFrames <= 1 ? 0 : frame / (durationInFrames - 1);
		setCamera(C, viewer, progress);
		settle(viewer).then(() => continueRender(frameHandle));
	}, [ready, frame, durationInFrames, mode]);

	return (
		<AbsoluteFill style={{backgroundColor: '#000'}}>
			<div ref={containerRef} style={{width, height, position: 'absolute'}} />
			{mode === 'city' ? (
				<div
					style={{
						position: 'absolute',
						top: 20,
						right: 24,
						color: 'white',
						font: '500 18px/1.2 sans-serif',
						textShadow: '0 1px 4px black',
					}}
				>
					For promotional purposes only
				</div>
			) : null}
		</AbsoluteFill>
	);
};
