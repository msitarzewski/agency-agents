export type LngLat = [number, number];

// Chaikin corner cutting turns a sparse route into a continuous curve. Repeated passes round
// direction changes into deliberate swerves instead of left-right heading bumps.
export const smoothFlightPath = (source: LngLat[], passes = 3): LngLat[] => {
	if (source.length < 2)
		throw new Error('Flyover path needs at least two points');

	// Keep adjacent longitudes continuous for routes that cross the antimeridian.
	const unwrapped: LngLat[] = [source[0]];
	for (let index = 1; index < source.length; index++) {
		const [lng, lat] = source[index];
		const previous = unwrapped[index - 1][0];
		let adjusted = lng;
		while (adjusted - previous > 180) adjusted -= 360;
		while (adjusted - previous < -180) adjusted += 360;
		unwrapped.push([adjusted, lat]);
	}

	let curve = unwrapped;
	for (let pass = 0; pass < Math.max(0, passes); pass++) {
		const next: LngLat[] = [curve[0]];
		for (let i = 0; i < curve.length - 1; i++) {
			const a = curve[i];
			const b = curve[i + 1];
			next.push(
				[a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25],
				[a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75],
			);
		}
		next.push(curve[curve.length - 1]);
		curve = next;
	}
	return curve;
};
