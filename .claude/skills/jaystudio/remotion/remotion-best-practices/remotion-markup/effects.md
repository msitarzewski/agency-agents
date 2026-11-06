---
name: effects
description: Canvas/WebGL visual effects for Remotion using effects arrays and createEffect().
metadata:
  tags: effects, visual-effects, webgl, canvas, video, create-effect
---

Read this guidance when adding an effect to a component that supports `effects`,
or when considering canvas post-processing or a reusable custom effect.

Docs: https://www.remotion.dev/docs/effects
Custom effect docs: https://www.remotion.dev/docs/create-effect

For exposure, white balance, Levels, Curves, and LUTs, read
[color-correction.md](color-correction.md).

## Usage

Install the package that provides the chosen effect:

```bash
npx remotion add @remotion/effects
```

Effects are functions passed to the `effects` prop of supported components.

These components accept `effects` directly:

| Import from        | Components                                                                                                                    |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `remotion`         | `<Img>`, `<CanvasImage>`, `<AnimatedImage>`, `<Solid>`, `<HtmlInCanvas>`                                                      |
| `@remotion/media`  | `<Video>`                                                                                                                     |
| `@remotion/gif`    | `<Gif>`                                                                                                                       |
| `@remotion/rive`   | `<RemotionRiveCanvas>`                                                                                                        |
| `@remotion/shapes` | `<Arrow>`, `<Callout>`, `<Circle>`, `<Ellipse>`, `<Heart>`, `<Pie>`, `<Polygon>`, `<Rect>`, `<Spark>`, `<Star>`, `<Triangle>` |

Ordinary HTML elements, `<Interactive.*>` DOM wrappers, `<AbsoluteFill>`, and
`<Sequence>` do not accept `effects` directly. To apply effects to their content,
wrap them in `<HtmlInCanvas>` and put the `effects` prop on the wrapper.

For example, apply an effect directly to a video:

```tsx
import {Video} from '@remotion/media';
import {blur} from '@remotion/effects/blur';

<Video
  src="https://remotion.media/video.mp4"
  effects={[blur({radius: 8})]}
/>;
```

Use the effect docs for exact props and imports. Most `@remotion/effects` imports use `@remotion/effects/<effect-slug>`; `uvTranslate()` and `xyTranslate()` use `@remotion/effects/translate`.

Most effects use WebGL2; `cylinder()`, `sphere()`, and `pageTurn()` use WebGPU. During renders, enable WebGL and WebGPU with:

```ts
import {Config} from '@remotion/cli/config';

Config.setChromiumOpenGlRenderer('angle');
```

## Available effects

Built-in effects from `@remotion/effects`:

- Color and tone: `brightness()`, `colorCorrection()`, `colorKey()`, `contrast()`, `curves()`, `duotone()`, `exposure()`, `grayscale()`, `hue()`, `invert()`, `levels()`, `linearGradient()`, `linearGradientTint()`, `lut()`, `saturation()`, `shadowsHighlights()`, `thermalVision()`, `tint()`, `vibrance()`, `whiteBalance()`.
- Blur and trails: `blur()`, `lightTrail()`, `linearProgressiveBlur()`, `radialProgressiveBlur()`, `regionBlur()`, `zoomBlur()`.
- Lighting: `dropShadow()`, `longShadows()`, `glow()`, `lightLeak()`, `shine()`, `starburst()`, `vignette()`.
- Distortion and transforms: `barrelDistortion()`, `chromaticAberration()`, `cornerPin()`, `fisheye()`, `mirror()`, `noiseDisplacement()`, `scale()`, `skew()`, `tile()`, `uvTranslate()`, `wave()`, `xyTranslate()`.
- Textures and patterns: `burlap()`, `checkerboard()`, `contourLines()`, `dotGrid()`, `emboss()`, `flannel()`, `gridlines()`, `halftone()`, `halftoneLinearGradient()`, `lines()`, `liquidContours()`, `noise()`, `paper()`, `pattern()`, `rings()`, `scanlines()`, `speckle()`, `tvSignalOff()`, `waves()`, `whiteNoise()`, `zigzag()`.
- Edges: `outline()`, `roughenEdges()`, `shrinkwrap()`, `tear()`.
- Pixelation and transitions: `evolve()`, `linearProgressivePixelate()`, `pixelate()`, `pixelDissolve()`, `radialProgressivePixelate()`, `venetianBlinds()`.

Example:

```tsx
import {Video} from '@remotion/media';
import {brightness} from '@remotion/effects/brightness';

<Video
  src="https://remotion.media/video.mp4"
  effects={[brightness({})]}
/>;
```

## Custom effects

Use `createEffect()` from `remotion` when the user wants a reusable effect factory that works in the same `effects` array as `@remotion/effects`.

Prefer a custom effect over `<HtmlInCanvas onPaint>` when the transformation should be reusable, parameterized, editable in Studio, or stackable with other effects.

For quick project-specific effects, keep the effect next to the composition, for example `src/effects/palette-map.ts`. For library effects intended for `@remotion/effects`, follow the repository's `add-effect` skill instead.

`createEffect()` expects:

- `type`: stable reverse-DNS identifier, for example `com.example.paletteMap`.
- `label`: Studio label, commonly `paletteMap()`.
- `documentationLink`: URL or `null`.
- `backend`: `"2d"`, `"webgl2"` or `"webgpu"`.
- `calculateKey(params)`: stable string containing every resolved parameter that changes output.
- `setup(target)`: create reusable backend state, or return `null`.
- `apply({source, target, width, height, params, state, flipSourceY})`: draw the transformed result into `target`.
- `cleanup(state)`: free resources created by `setup()`.
- `schema`: an `InteractivitySchema` for Studio controls. `disabled` is added automatically.
- `validateParams(params)`: throw on missing or invalid values.

Use `backend: "2d"` for simple pixel, filter, drawImage, or image-data effects. Use WebGL2 only when shader math or GPU performance is needed; during renders, enable WebGL as shown above.

```ts
import {createEffect, type InteractivitySchema} from 'remotion';

type MyEffectParams = {
  readonly amount?: number;
};

const myEffectSchema = {
  amount: {
    type: 'number',
    min: 0,
    max: 1,
    step: 0.01,
    default: 1,
    description: 'Amount',
  },
} as const satisfies InteractivitySchema;

const resolve = (params: MyEffectParams) => ({
  amount: params.amount ?? 1,
});

export const myEffect = createEffect<MyEffectParams, null>({
  type: 'com.example.myEffect',
  label: 'myEffect()',
  documentationLink: null,
  backend: '2d',
  calculateKey: (params) => {
    const {amount} = resolve(params);
    return `my-effect-${amount}`;
  },
  setup: () => null,
  apply: ({source, target, width, height, params}) => {
    const ctx = target.getContext('2d');
    if (!ctx) {
      throw new Error('Could not get a 2D context for myEffect().');
    }

    const {amount} = resolve(params);

    ctx.clearRect(0, 0, width, height);
    ctx.filter = `opacity(${amount * 100}%)`;
    ctx.drawImage(source, 0, 0, width, height);
    ctx.filter = 'none';
  },
  cleanup: () => undefined,
  schema: myEffectSchema,
  validateParams: ({amount = 1}) => {
    if (typeof amount !== 'number' || !Number.isFinite(amount) || amount < 0 || amount > 1) {
      throw new TypeError('amount must be a number between 0 and 1');
    }
  },
});
```

For a WebGL2 effect, compile/link shaders in `setup()`, keep the program, fullscreen quad, texture, and uniform locations in state, upload `source` in `apply()`, and free GPU resources in `cleanup()`. Minimal shape:

```ts
import {createEffect, type InteractivitySchema} from 'remotion';

type RgbShiftParams = {
  readonly amount?: number;
};

type RgbShiftState = {
  readonly gl: WebGL2RenderingContext;
  readonly program: WebGLProgram;
  readonly vao: WebGLVertexArrayObject;
  readonly vbo: WebGLBuffer;
  readonly texture: WebGLTexture;
  readonly uSource: WebGLUniformLocation | null;
  readonly uOffset: WebGLUniformLocation | null;
};

const rgbShiftSchema = {
  amount: {
    type: 'number',
    min: 0,
    max: 80,
    step: 1,
    default: 12,
    description: 'Amount',
  },
} as const satisfies InteractivitySchema;

export const rgbShift = createEffect<RgbShiftParams, RgbShiftState>({
  type: 'com.example.rgbShift',
  label: 'rgbShift()',
  documentationLink: null,
  backend: 'webgl2',
  calculateKey: ({amount = 12}) => `rgb-shift-${amount}`,
  setup: (target) => {
    const gl = target.getContext('webgl2', {
      premultipliedAlpha: true,
      alpha: true,
      preserveDrawingBuffer: true,
    });
    if (!gl) {
      throw new Error('Could not get a WebGL2 context for rgbShift().');
    }

    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);

    // Compile/link shaders, create a fullscreen quad VAO/VBO, create a
    // CLAMP_TO_EDGE RGBA texture, and get uSource/uOffset uniform locations.
    return createRgbShiftState(gl);
  },
  apply: ({source, width, height, params, state, flipSourceY}) => {
    const amount = params.amount ?? 12;
    const {gl} = state;

    gl.viewport(0, 0, width, height);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, flipSourceY);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, state.texture);
    gl.texImage2D(
      gl.TEXTURE_2D,
      0,
      gl.RGBA,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      source as TexImageSource,
    );

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.useProgram(state.program);
    if (state.uSource) gl.uniform1i(state.uSource, 0);
    if (state.uOffset) gl.uniform2f(state.uOffset, amount / width, 0);
    gl.bindVertexArray(state.vao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  },
  cleanup: ({gl, program, vao, vbo, texture}) => {
    gl.deleteTexture(texture);
    gl.deleteBuffer(vbo);
    gl.deleteProgram(program);
    gl.deleteVertexArray(vao);
  },
  schema: rgbShiftSchema,
  validateParams: ({amount = 12}) => {
    if (typeof amount !== 'number' || !Number.isFinite(amount) || amount < 0 || amount > 80) {
      throw new TypeError('amount must be a number between 0 and 80');
    }
  },
});
```

For a complete 2D and WebGL2 pair, see `packages/example/src/EffectsTestbed/sample-posterize-2d.ts` and `packages/example/src/EffectsTestbed/sample-rgb-shift-webgl.ts`.

Use the returned factory in an `effects` array:

```tsx
import {CanvasImage, staticFile} from 'remotion';
import {myEffect} from './effects/my-effect';

export const MyComp: React.FC = () => {
  return (
    <CanvasImage
      src={staticFile('image.png')}
      effects={[myEffect({amount: 0.8})]}
    />
  );
};
```

When generating a custom effect, also:

- Include `disabled?: boolean` only through the returned factory; do not add it to the custom params type or schema.
- Validate required parameters at factory-call time with `validateParams`.
- Include all defaults in both `schema` and the `resolve()` helper.
- Reset mutable 2D context state such as `filter`, `globalAlpha`, transforms, and compositing after drawing.
- Preserve alpha unless the requested effect intentionally changes transparency.
