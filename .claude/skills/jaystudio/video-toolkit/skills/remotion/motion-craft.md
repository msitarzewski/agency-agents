# Motion Craft

Numbers and rules for how things move in a toolkit video, and the defaults that make a video look generated.
Read this before animating a scene, and again when a scene "feels off" in review. These are defaults: a brand
guideline, a reference the user gave, or a deliberate choice for one moment wins over them.

All frame counts are at the toolkit's 30fps.

> Adapted from the motion and review references of [HyperFrames](https://github.com/heygen-com/hyperframes)
> (HeyGen, Apache-2.0), which measured them frame by frame from their launch films, and translated from
> GSAP to Remotion's `interpolate`, `Easing` and `spring`.

## Moves

| Rule | Seconds | Frames |
|------|---------|--------|
| A fast move (card, panel, camera punch) | 0.3-0.6 s | 9-18 |
| An exit is shorter than its entrance | 40-50% shorter | an 18f entrance exits in ~10f |
| Next element starts when the previous one is | 30-50% done | |
| Stagger: letters | 1 frame apart | 1 |
| Stagger: words | 60-120 ms | 2-4 |
| Stagger: list items, cards | 40-80 ms | 1-2 |

- **Arrive slow, leave clean.** Arrivals land on a long tail; landing takes longer than leaving. An exit is one
  smooth motion, never slide, stop, then leave. An entrance that is too snappy reads as a glitch.
- **One move is one interpolation.** Don't chain two tweens to fake an ease.
- **Fully sequential looks robotic, all at once looks cheap.** Overlap is the middle (the 30-50% rule above).

## Ease by role

Using the same ease at the same duration on everything is the flat default that makes a video feel generated.
Choose the ease from what the move does:

| Role | Ease | Remotion |
|------|------|----------|
| Arrival (an element lands) | long-tailed ease-out | `Easing.out(Easing.exp)` or `Easing.out(Easing.poly(5))` |
| Camera move, colour flood | ease both ways | `Easing.inOut(Easing.cubic)` |
| Exit, zoom *through* something | accelerate | `Easing.in(Easing.poly(4))` |
| Rotation, progress bar, constant speed that is the point | linear | `Easing.linear` |

```tsx
const enter = interpolate(frame, [0, 18], [0, 1], {
  easing: Easing.out(Easing.exp),
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
```

## Springs

Name a spring by its **damping ratio** ζ, not by its raw numbers. For Remotion's `spring()`,
ζ = `damping / (2 * sqrt(stiffness * mass))`. Remotion's default (`damping: 10, stiffness: 100, mass: 1`) is
ζ = 0.5, which is playful, not neutral.

| ζ | Reads as | `damping` at stiffness 100, mass 1 |
|---|----------|------------------------------------|
| 1.0 | never bounces | 20 |
| 0.7-0.85 | premium, settled | 14-17 |
| 0.4-0.6 | playful | 8-12 |
| < 0.3 | cartoon | < 6 |

Position and size may bounce. **Opacity and colour never do**: drive them with `interpolate`, or clamp the spring
(`overshootClamping: true`). UI elements should not bounce at all (ζ = 1) unless the brand is playful.

## Titles and text

- **A landed title is dead still.** The motion moves on to the next element, the camera or the background. No
  slow creep, drift, breathing or scale after it lands.
- **Vary the entrance within a video.** Fade-and-slide-up on every title is the most common tell. Alternatives:
  - per word: `blur(6px)` → 0 and opacity 0 → 1 over 4 frames, words 2 frames apart, no translate;
  - per word from light grey to ink, 2-3 frames apart, no position change;
  - the whole line blurring in, 8px → 0 over 4-6 frames;
  - per letter for a name, 3 frames apart, opacity 0.3 → 1 with a slight blur;
  - one word rolling through options like a slot machine, about 3 frames a roll.
- **Read time.** A line the viewer must read holds **0.5 s + 0.3 s per word**. A one- or two-word chapter line
  may hold 0.4 s. The video's last line holds at least 2 s. Narrated lines also have to outlast their words in the
  voiceover.
- **Exit text** with a blur-out and fade of 4-8 frames, word by word, or with the scene's move.
- **Size.** Titles 4-9% of the frame height (43-97px at 1080p), one or two lines. Body and quiet lines 2.5-4%.
  Nothing a viewer must read under ~2.6% of the frame's short side (28px at 1080p, 21px on the 1440x810
  synthetic-demo canvas). Highlight one word in the accent colour, and only a word that carries meaning.

## Rhythm

- **Contrast speeds.** Montages cut every 4-24 frames. A UI demo holds one framing for 7-10 s while the UI acts.
  Most shots run 1.8-3 s with motion inside them.
- **Hold 0.3-0.75 s (9-22 frames) before the payoff**, then play the payoff at normal speed.
- **No dead air.** More than ~3 s where nothing on screen changes reads as a stall, unless it is a deliberate
  hold. Give the hold a real next action (the cursor heading to the next control, the camera's next move).
  Don't add a slow drift, a blinking caret or a loop to fill it.
- **Continuous motion that works:** the product's UI doing something, footage playing, a slow orbit of a
  background (3-5° a second).

## Beat grid (cutting to music)

Frames per beat = `fps * 60 / bpm`. Compute each beat from its index and round once:

```ts
const beatFrame = (i: number) => Math.round((i * fps * 60) / bpm);
```

Never add a rounded beat length repeatedly. At 128 BPM and 30fps that drifts 2 frames in 32 beats. Cut on the
beat, change the layout on the bar (every 4 beats).

## Transitions with a cause

Use 3-5 kinds of transition in a video, and give each one a cause on screen. Hard cuts belong inside a scene
(punch-ins). At most about a third of the seams between scenes should be hard cuts.

| Transition | How it is built |
|------------|-----------------|
| Zoom through a button | camera tracks to the button (~18f), then the button scales from ~8% to ~250% of the frame in ~10f on a strong ease-in; its fill becomes the next scene |
| Object becomes the world | a card grows past the frame in ~20f, ease-in-out, its corner radius shrinking; what surrounds it blurs ~15px and fades in ~9f; the next content fades in while it still grows |
| Morph | one container widens into the next (icon card → prompt box) in ~6f, `Easing.out(Easing.poly(4))`, with a horizontal blur 12px → 0 |
| Carry across | the result shrinks 1 → 0.6, blur peaking at 6px mid-move, and lands inside the next screen as it builds around it |
| Colour flood | the hero object stays while the whole background changes colour in ~12f, `Easing.inOut(Easing.cubic)` |
| Whip | a horizontal or vertical smear of 4-9f; the arriving element lands blurred and sharpens in ~4f |
| Iris from the click | `clip-path: circle()` opens from the clicked point onto the next scene in ~5f |
| Dip cut | the outgoing frame darkens ~40% for 3 frames before a hard cut, so the cut reads as intended |
| Blur swap | out: opacity → 0 with ~8px blur in 4-6f; in: blur → 0 in 4f; the background never cuts |

**Cut at the fastest frame of a move**, with matching direction and speed on both sides. A click into a new
screen is a match cut on the click: the new screen comes in slightly large and settles.

The toolkit's `lib/transitions` (`glitch`, `rgbSplit`, `lightLeak`, `pixelate`, `checkerboard`, ...) are
decorative. They fit when the content gives them a reason (a glitch on a "broken" problem scene, a light leak on
a celebration), not as the seam between every pair of scenes.

## Defaults that look generated

Generated video falls into these when nothing has been decided. Treat each as **off by default**. Use one only
when the brand's own material or the user's reference uses it, and then only the way they use it.

- a black or dark navy void as the background, with small elements floating in the middle;
- glow, bloom, neon, lens flares, glowing orbs and rings; floating particles or shapes as decoration;
- purple or blue gradients, mesh gradients, glass cards;
- a cream paper background with a serif display, italic accent words, numbered "01 / 02" labels, small
  monospace caps labels and pill chips;
- everything centred; everything fading in at once; every element fading and sliding up;
- text that moves while it is read; titles that keep drifting or scaling after they land;
- breathing, floating or pulsing loops standing in for motion on titles and UI;
- bounce on UI; click rings;
- every scene entering the same way;
- corner labels, frame borders, corner brackets, HUD readouts as decoration;
- three cards in a row, KPI grids, a title over a dimmed screenshot;
- the logo docked in a corner.

Some toolkit pieces produce these by default, so pick them deliberately rather than leaving them in:

| Toolkit piece | Default that lands on the list |
|---------------|--------------------------------|
| `AnimatedBackground` | floating shapes as decoration |
| product-demo template | dark background, stats cards in a row |
| `LogoWatermark` | logo docked in a corner |
| `Cursor` | a ripple on every click (a click ring) |
| `PointingHand` | pulse loop |

When a scene shows one of these, name it, replace it with something taken from the subject, the brand or the
medium, and note the decision in the scene's `designNotes` in `project.json` so later sessions don't reintroduce
it.

## Reviewing a scene against this

When a scene feels weak in `/scene-review` or `/design`, step through it in Remotion Studio and ask:

- **Does it read as what it is?** Describe the frame in one sentence as a stranger would. If you have to explain
  an object, it's the first thing to fix.
- **Where does the eye go?** One focal point per frame, and the subject separates from the background.
- **Timing as a first-time viewer:** is each line on screen long enough to read? Does anything pop on with no
  move? Does everything move at once on the same curve?
- **Tells:** which items of the list above are on screen?
- **The pictures alone:** with the narration muted, do the key frames still tell the story?

Write each problem as one line, `t=4.2s · where · problem → exact change`, and fix text first, then timing, then
detail. A scene that feels busy: remove a third of the motion and keep the moves that lead the eye.
