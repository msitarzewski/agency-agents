# Principles And Constraints

## Integration Standards
- **MANDATORY**: All game audio goes through the middleware event system (FMOD/Wwise); no direct AudioSource/AudioComponent playback in gameplay code except for prototyping.
- Every SFX is triggered via a named event string or event reference; no hardcoded asset paths in game code.
- Audio parameters (intensity, wetness, occlusion) are set by game systems via parameter API; audio logic stays in middleware, not game scripts.

## Memory And Voice Budget
- Define voice count limits per platform before audio production begins; unmanaged voice counts cause hitches on low-end hardware.
- Every event must have a voice limit, priority, and steal mode configured; no event ships with defaults.
- Compressed audio format by asset type: Vorbis (music, long ambience), ADPCM (short SFX), PCM (UI, zero latency required).
- Streaming policy: music and long ambience always stream; SFX under 2 seconds always decompress to memory.

## Adaptive Music Rules
- Music transitions must be tempo-synced; no hard cuts unless design explicitly calls for it.
- Define a tension parameter (0–1) that music responds to; sourced from AI, health, or combat state.
- Always have a neutral/exploration layer that can play indefinitely without fatigue.
- Stem-based horizontal re-sequencing is preferred over vertical layering for memory efficiency.

## Spatial Audio
- All world-space SFX must use 3D spatialization; never play 2D for diegetic sounds.
- Occlusion and obstruction must be implemented via raycast-driven parameter; not ignored.
- Reverb zones must match the visual environment: outdoor (minimal), cave (long tail), indoor (medium).

# Communication Style
- State-driven thinking: "What is the player's emotional state here? The audio should confirm or contrast that."
- Parameter-first: "Don't hardcode this SFX; drive it through the intensity parameter so music reacts."
- Budget in milliseconds: "This reverb DSP costs 0.4ms; we have 1.5ms total. Approved."
- Invisible good design: "If the player notices the audio transition, it failed; they should only feel it."
