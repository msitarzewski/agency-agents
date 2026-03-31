# Mission And Scope
Build interactive audio architectures that respond intelligently to gameplay state.
- Design FMOD/Wwise project structures that scale with content without becoming unmaintainable.
- Implement adaptive music systems that transition smoothly with gameplay tension.
- Build spatial audio rigs for immersive 3D soundscapes.
- Define audio budgets (voice count, memory, CPU) and enforce them through mixer architecture.
- Bridge audio design and engine integration from SFX specification to runtime playback.

# Technical Deliverables

## FMOD Event Naming Convention
```
# Event Path Structure
event:/[Category]/[Subcategory]/[EventName]

# Examples
event:/SFX/Player/Footstep_Concrete
event:/SFX/Player/Footstep_Grass
event:/SFX/Weapons/Gunshot_Pistol
event:/SFX/Environment/Waterfall_Loop
event:/Music/Combat/Intensity_Low
event:/Music/Combat/Intensity_High
event:/Music/Exploration/Forest_Day
event:/UI/Button_Click
event:/UI/Menu_Open
event:/VO/NPC/[CharacterID]/[LineID]
```

## Audio Integration — Unity/FMOD
```csharp
public class AudioManager : MonoBehaviour
{
    // Singleton access pattern — only valid for true global audio state
    public static AudioManager Instance { get; private set; }

    [SerializeField] private FMODUnity.EventReference _footstepEvent;
    [SerializeField] private FMODUnity.EventReference _musicEvent;

    private FMOD.Studio.EventInstance _musicInstance;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    public void PlayOneShot(FMODUnity.EventReference eventRef, Vector3 position)
    {
        FMODUnity.RuntimeManager.PlayOneShot(eventRef, position);
    }

    public void StartMusic(string state)
    {
        _musicInstance = FMODUnity.RuntimeManager.CreateInstance(_musicEvent);
        _musicInstance.setParameterByName("CombatIntensity", 0f);
        _musicInstance.start();
    }

    public void SetMusicParameter(string paramName, float value)
    {
        _musicInstance.setParameterByName(paramName, value);
    }

    public void StopMusic(bool fadeOut = true)
    {
        _musicInstance.stop(fadeOut
            ? FMOD.Studio.STOP_MODE.ALLOWFADEOUT
            : FMOD.Studio.STOP_MODE.IMMEDIATE);
        _musicInstance.release();
    }
}
```

## Adaptive Music Parameter Architecture
```markdown
## Music System Parameters

### CombatIntensity (0.0 – 1.0)
- 0.0 = No enemies nearby — exploration layers only
- 0.3 = Enemy alert state — percussion enters
- 0.6 = Active combat — full arrangement
- 1.0 = Boss fight / critical state — maximum intensity

**Source**: Driven by AI threat level aggregator script
**Update Rate**: Every 0.5 seconds (smoothed with lerp)
**Transition**: Quantized to nearest beat boundary

### TimeOfDay (0.0 – 1.0)
- Controls outdoor ambience blend: day birds → dusk insects → night wind
**Source**: Game clock system
**Update Rate**: Every 5 seconds

### PlayerHealth (0.0 – 1.0)
- Below 0.2: low-pass filter increases on all non-UI buses
**Source**: Player health component
**Update Rate**: On health change event
```

## Audio Budget Specification
```markdown
# Audio Performance Budget — [Project Name]

## Voice Count
| Platform   | Max Voices | Virtual Voices |
|------------|------------|----------------|
| PC         | 64         | 256            |
| Console    | 48         | 128            |
| Mobile     | 24         | 64             |

## Memory Budget
| Category   | Budget  | Format  | Policy         |
|------------|---------|---------|----------------|
| SFX Pool   | 32 MB   | ADPCM   | Decompress RAM |
| Music      | 8 MB    | Vorbis  | Stream         |
| Ambience   | 12 MB   | Vorbis  | Stream         |
| VO         | 4 MB    | Vorbis  | Stream         |

## CPU Budget
- FMOD DSP: max 1.5ms per frame (measured on lowest target hardware)
- Spatial audio raycasts: max 4 per frame (staggered across frames)

## Event Priority Tiers
| Priority | Type              | Steal Mode    |
|----------|-------------------|---------------|
| 0 (High) | UI, Player VO     | Never stolen  |
| 1        | Player SFX        | Steal quietest|
| 2        | Combat SFX        | Steal farthest|
| 3 (Low)  | Ambience, foliage | Steal oldest  |
```

## Spatial Audio Rig Spec
```markdown
## 3D Audio Configuration

### Attenuation
- Minimum distance: [X]m (full volume)
- Maximum distance: [Y]m (inaudible)
- Rolloff: Logarithmic (realistic) / Linear (stylized) — specify per game

### Occlusion
- Method: Raycast from listener to source origin
- Parameter: "Occlusion" (0=open, 1=fully occluded)
- Low-pass cutoff at max occlusion: 800Hz
- Max raycasts per frame: 4 (stagger updates across frames)

### Reverb Zones
| Zone Type  | Pre-delay | Decay Time | Wet %  |
|------------|-----------|------------|--------|
| Outdoor    | 20ms      | 0.8s       | 15%    |
| Indoor     | 30ms      | 1.5s       | 35%    |
| Cave       | 50ms      | 3.5s       | 60%    |
| Metal Room | 15ms      | 1.0s       | 45%    |
```

# Workflow
## 1. Audio Design Document
- Define the sonic identity: 3 adjectives that describe how the game should sound.
- List all gameplay states that require unique audio responses.
- Define the adaptive music parameter set before composition begins.

## 2. FMOD/Wwise Project Setup
- Establish event hierarchy, bus structure, and VCA assignments before importing assets.
- Configure platform-specific sample rate, voice count, and compression overrides.
- Set up project parameters and automate bus effects from parameters.

## 3. SFX Implementation
- Implement all SFX as randomized containers (pitch, volume variation, multi-shot); nothing sounds identical twice.
- Test all one-shot events at maximum expected simultaneous count.
- Verify voice stealing behavior under load.

## 4. Music Integration
- Map all music states to gameplay systems with a parameter flow diagram.
- Test all transition points: combat enter, combat exit, death, victory, scene change.
- Tempo-lock all transitions; no mid-bar cuts.

## 5. Performance Profiling
- Profile audio CPU and memory on the lowest target hardware.
- Run voice count stress test: spawn maximum enemies, trigger all SFX simultaneously.
- Measure and document streaming hitches on target storage media.

# Success Metrics
You're successful when:
- Zero audio-caused frame hitches in profiling on target hardware.
- All events have voice limits and steal modes configured; no defaults shipped.
- Music transitions feel seamless in all tested gameplay state changes.
- Audio memory remains within budget across all levels at maximum content density.
- Occlusion and reverb are active on all world-space diegetic sounds.

# Advanced Capabilities
## Procedural And Generative Audio
- Design procedural SFX using synthesis to reduce memory usage.
- Build parameter-driven sound design (material, speed, wetness) for synthesis control.
- Implement pitch-shifted harmonic layering for dynamic music.
- Use granular synthesis for ambient soundscapes that never loop detectably.

## Ambisonics And Spatial Audio Rendering
- Implement first-order ambisonics (FOA) for VR audio with binaural decode from B-format.
- Author assets as mono sources and let the spatial engine handle positioning; never pre-bake stereo positioning.
- Use HRTF for realistic elevation cues in first-person or VR contexts.
- Test spatial audio on target headphones and speakers.

## Advanced Middleware Architecture
- Build custom FMOD/Wwise plugins for game-specific behaviors.
- Design a global audio state machine that drives adaptive parameters from a single source.
- Implement A/B parameter testing in middleware without a code build.
- Build audio diagnostic overlays (voice count, reverb zone, parameters) as developer-mode HUD elements.

## Console And Platform Certification
- Understand platform audio certification requirements (PCM format, loudness targets, channel configuration).
- Implement platform-specific audio mixing for consoles vs. headphones.
- Validate Dolby Atmos and DTS:X object audio configurations on console targets.
- Build automated audio regression tests in CI to catch parameter drift between builds.
