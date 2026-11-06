// Example tokens only. Replace every visual value with production-local tokens.
export const COLORS = {
	bg: '#101315',
	// Electric water — a near-white icy core with a blue glow and a white-hot draw-head (the "electricity"
	// travels along the river as it draws on). No dark casing.
	river: '#E8F7FF', // bright icy core
	riverGlow: 'rgba(73,198,255,0.5)', // electric-blue glow
	riverHead: '#FFFFFF', // white-hot leading head
	riverHeadGlow: 'rgba(120,225,255,0.95)',
	border: '#f5f2ed', // neutral cream country borders/labels over the colored fills
	cream: '#f5f0eb',
} as const;

// Example progressive fill tokens. Rename these keys and replace values for each production.
export const COUNTRY = {
	china: '#D4A853',
	india: '#5B8A8A',
	bangladesh: '#C07B57',
} as const;
// Darker shade of each country colour — the settled border line (the bright COUNTRY colour is the
// glowing draw-head that leads the animation).
export const COUNTRY_DARK = {
	china: '#9A7530',
	india: '#3C5C5C',
	bangladesh: '#855239',
} as const;
export const FILL_OPACITY = 0.5;

export const VIDEO = {width: 1920, height: 1080, fps: 30} as const;

// Beat durations (seconds → frames at VIDEO.fps)
export const DUR = {
	mapExplainer: 12 * VIDEO.fps,
} as const;
