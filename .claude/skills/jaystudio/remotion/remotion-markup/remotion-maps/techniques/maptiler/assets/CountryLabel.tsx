import React from 'react';
import {Easing, interpolate} from 'remotion';

// Reusable country label. Supply typography and final values from the consuming project; the CSS custom
// properties below provide neutral fallbacks. Positioned by its centre (x,y in screen px).
export const CountryLabel: React.FC<{
	name: string;
	color: string;
	reveal: number;
	x: number;
	y: number;
}> = ({name, color, reveal, x, y}) => {
	const e = interpolate(reveal, [0, 1], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.bezier(0.3333333333333333, 1, 0.6666666666666666, 1),
	});
	return (
		<div
			style={{
				position: 'absolute',
				left: x,
				top: y,
				transform: 'translate(-50%, -50%)',
				pointerEvents: 'none',
				display: 'flex',
				flexDirection: 'column',
				alignItems: 'center',
				opacity: e,
			}}
		>
			<div
				style={{
					transform: `translateY(${(1 - e) * 16}px)`,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
				}}
			>
				{/* accent rule — draws out from the centre in the country's colour */}
				<div
					style={{
						width: 64,
						height: 3,
						borderRadius: 2,
						background: color,
						transform: `scaleX(${e})`,
						boxShadow: `0 0 10px ${color}`,
					}}
				/>
				<div
					style={{
						fontFamily: 'var(--map-label-font, system-ui, sans-serif)',
						fontWeight: 'var(--map-label-weight, 600)',
						fontSize: 'var(--map-label-size, 34px)',
						letterSpacing: 'var(--map-label-tracking, 0.16em)',
						textTransform: 'uppercase',
						color: 'var(--map-label-color, #ffffff)',
						textShadow: 'var(--map-label-shadow, 0 2px 18px rgba(0,0,0,0.9))',
						marginTop: 13,
						paddingLeft: 'var(--map-label-tracking, 0.16em)',
						whiteSpace: 'nowrap',
					}}
				>
					{name}
				</div>
			</div>
		</div>
	);
};
