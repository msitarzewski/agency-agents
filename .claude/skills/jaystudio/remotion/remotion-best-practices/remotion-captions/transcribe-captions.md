# Transcribing audio

To transcribe audio to generate captions in Remotion, use the [`transcribe()`](https://www.remotion.dev/docs/whisper-webgpu/transcribe.md) function from the [`@remotion/whisper-webgpu`](https://www.remotion.dev/docs/whisper-webgpu.md) package.
It runs Whisper locally on the GPU and works in both Node.js and the browser.

## Prerequisites

Install the required packages if they are not installed:

```bash
npx remotion add @remotion/whisper-webgpu @huggingface/transformers mediabunny @mediabunny/server # If project uses npm
bunx remotion add @remotion/whisper-webgpu @huggingface/transformers mediabunny @mediabunny/server # If project uses bun
yarn remotion add @remotion/whisper-webgpu @huggingface/transformers mediabunny @mediabunny/server # If project uses yarn
pnpm exec remotion add @remotion/whisper-webgpu @huggingface/transformers mediabunny @mediabunny/server # If project uses pnpm
```

A compatible GPU is required. ONNX Runtime does not work on Linux arm64.

## Transcribing

Make a Node.js script that decodes the audio to a 16kHz mono waveform, downloads a model, and transcribes it.

```ts
import { registerMediabunnyServer } from "@mediabunny/server";
import {
  WHISPER_WEBGPU_SAMPLE_RATE,
  canUseWhisperWebGpu,
  downloadWhisperModel,
  loadWhisperModel,
  toCaptions,
  transcribe,
} from "@remotion/whisper-webgpu";
import {
  ALL_FORMATS,
  Conversion,
  FilePathSource,
  Input,
  NullTarget,
  Output,
  WavOutputFormat,
} from "mediabunny";
import { writeFile } from "node:fs/promises";

registerMediabunnyServer();

const support = await canUseWhisperWebGpu();
if (!support.supported) {
  throw new Error(support.detailedReason);
}

type WaveformChunk = {
  startFrame: number;
  waveform: Float32Array;
};
const chunks: WaveformChunk[] = [];

using input = new Input({
  formats: ALL_FORMATS,
  source: new FilePathSource("public/video123.mp4"),
});
const audioTrack = await input.getPrimaryAudioTrack();
if (audioTrack === null) {
  throw new Error("The media does not contain an audio track.");
}

const conversion = await Conversion.init({
  input,
  output: new Output({
    format: new WavOutputFormat(),
    target: new NullTarget(),
  }),
  video: { discard: true },
  audio: (track) => {
    if (track.id !== audioTrack.id) {
      return { discard: true };
    }

    return {
      codec: "pcm-f32",
      forceTranscode: true,
      numberOfChannels: 1,
      sampleFormat: "f32",
      sampleRate: WHISPER_WEBGPU_SAMPLE_RATE,
      process: (sample) => {
        const waveform = new Float32Array(
          sample.allocationSize({ format: "f32", planeIndex: 0 }) /
            Float32Array.BYTES_PER_ELEMENT,
        );
        sample.copyTo(waveform, { format: "f32", planeIndex: 0 });
        chunks.push({
          startFrame: Math.round(sample.timestamp * WHISPER_WEBGPU_SAMPLE_RATE),
          waveform,
        });
        return sample;
      },
    };
  },
});

if (!conversion.isValid) {
  throw new Error("The audio track cannot be decoded.");
}

await conversion.execute();

const waveformLength = chunks.reduce(
  (max, chunk) => Math.max(max, chunk.startFrame + chunk.waveform.length),
  0,
);
const channelWaveform = new Float32Array(waveformLength);
for (const chunk of chunks) {
  const destinationStart = Math.max(0, chunk.startFrame);
  const sourceStart = Math.max(0, -chunk.startFrame);
  const availableLength = Math.min(
    chunk.waveform.length - sourceStart,
    channelWaveform.length - destinationStart,
  );

  if (availableLength > 0) {
    channelWaveform.set(
      chunk.waveform.subarray(sourceStart, sourceStart + availableLength),
      destinationStart,
    );
  }
}

const model = "small.en";
await downloadWhisperModel({ model });
await using modelHandle = await loadWhisperModel({ model });
const transcription = await transcribe({ channelWaveform, model });
const { captions } = toCaptions({ whisperWebGpuOutput: transcription });

// Write it to a file so the captions can be inlined into the Remotion code
await writeFile("captions123.json", JSON.stringify(captions, null, 2));
```

## Choosing a model

`small.en` is the recommended default for English.  
For other languages, use a multilingual model such as `small` and pass the `language` option to `transcribe()` - automatic language detection is not supported.  
See [`getAvailableModels()`](https://www.remotion.dev/docs/whisper-webgpu/get-available-models.md) for all models.

## Transcribing in the browser

In the browser, use [`resampleTo16Khz()`](https://www.remotion.dev/docs/whisper-webgpu/resample-to-16khz.md) to get the waveform from a `File` instead of using Mediabunny:

```ts
import {
  downloadWhisperModel,
  resampleTo16Khz,
  toCaptions,
  transcribe,
} from "@remotion/whisper-webgpu";

export const transcribeFile = async (file: File) => {
  await downloadWhisperModel({ model: "small.en" });
  const channelWaveform = await resampleTo16Khz({ file });
  const transcription = await transcribe({
    channelWaveform,
    model: "small.en",
  });

  const { captions } = toCaptions({ whisperWebGpuOutput: transcription });
  return captions;
};
```

Transcribe each original source video or audio file individually.  
Keep the resulting caption timestamps relative to the beginning of that source file, including portions currently trimmed out of the edit.  
Do not add composition offsets or flatten multiple transcripts into composition-wide timestamps.

See [Displaying captions](display-captions.md) for how to display the captions in Remotion.
