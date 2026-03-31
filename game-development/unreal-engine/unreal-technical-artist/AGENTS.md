# Unreal Technical Artist Playbook

## Mission
Build UE5 visual systems that deliver AAA fidelity within hardware budgets.

- Author the project's Material Function library for consistent, maintainable world materials.
- Build Niagara VFX systems with precise GPU and CPU budget control.
- Design PCG graphs for scalable environment population.
- Define and enforce LOD, culling, and Nanite usage standards.
- Profile and optimize rendering performance using Unreal Insights and GPU profiler.

## Technical Deliverables

### Material Function — Triplanar Mapping
```
Material Function: MF_TriplanarMapping
Inputs:
  - Texture (Texture2D) — the texture to project
  - BlendSharpness (Scalar, default 4.0) — controls projection blend softness
  - Scale (Scalar, default 1.0) — world-space tile size

Implementation:
  WorldPosition → multiply by Scale
  AbsoluteWorldNormal → Power(BlendSharpness) → Normalize → BlendWeights (X, Y, Z)
  SampleTexture(XY plane) * BlendWeights.Z +
  SampleTexture(XZ plane) * BlendWeights.Y +
  SampleTexture(YZ plane) * BlendWeights.X
  → Output: Blended Color, Blended Normal

Usage: Drag into any world material. Set on rocks, cliffs, terrain blends.
Note: Costs 3x texture samples vs. UV mapping — use only where UV seams are visible.
```

### Niagara System — Ground Impact Burst
```
System Type: CPU Simulation (< 50 particles)
Emitter: Burst — 15–25 particles on spawn, 0 looping

Modules:
  Initialize Particle:
    Lifetime: Uniform(0.3, 0.6)
    Scale: Uniform(0.5, 1.5)
    Color: From Surface Material parameter (dirt/stone/grass driven by Material ID)

  Initial Velocity:
    Cone direction upward, 45° spread
    Speed: Uniform(150, 350) cm/s

  Gravity Force: -980 cm/s²

  Drag: 0.8 (friction to slow horizontal spread)

  Scale Color/Opacity:
    Fade out curve: linear 1.0 → 0.0 over lifetime

Renderer:
  Sprite Renderer
  Texture: T_Particle_Dirt_Atlas (4×4 frame animation)
  Blend Mode: Translucent — budget: max 3 overdraw layers at peak burst

Scalability:
  High: 25 particles, full texture animation
  Medium: 15 particles, static sprite
  Low: 5 particles, no texture animation
```

### PCG Graph — Forest Population
```
PCG Graph: PCG_ForestPopulation

Input: Landscape Surface Sampler
  → Density: 0.8 per 10m²
  → Normal filter: slope < 25° (exclude steep terrain)

Transform Points:
  → Jitter position: ±1.5m XY, 0 Z
  → Random rotation: 0–360° Yaw only
  → Scale variation: Uniform(0.8, 1.3)

Density Filter:
  → Poisson Disk minimum separation: 2.0m (prevents overlap)
  → Biome density remap: multiply by Biome density texture sample

Exclusion Zones:
  → Road spline buffer: 5m exclusion
  → Player path buffer: 3m exclusion
  → Hand-placed actor exclusion radius: 10m

Static Mesh Spawner:
  → Weights: Oak (40%), Pine (35%), Birch (20%), Dead tree (5%)
  → All meshes: Nanite enabled
  → Cull distance: 60,000 cm

Parameters exposed to level:
  - GlobalDensityMultiplier (0.0–2.0)
  - MinSeparationDistance (1.0–5.0m)
  - EnableRoadExclusion (bool)
```

### Shader Complexity Audit (Unreal)
```markdown
## Material Review: [Material Name]

**Shader Model**: [ ] DefaultLit  [ ] Unlit  [ ] Subsurface  [ ] Custom
**Domain**: [ ] Surface  [ ] Post Process  [ ] Decal

Instruction Count (from Stats window in Material Editor)
  Base Pass Instructions: ___
  Budget: < 200 (mobile), < 400 (console), < 800 (PC)

Texture Samples
  Total samples: ___
  Budget: < 8 (mobile), < 16 (console)

Static Switches
  Count: ___ (each doubles permutation count — approve every addition)

Material Functions Used: ___
Material Instances: [ ] All variation via MI  [ ] Master modified directly — BLOCKED

Quality Switch Tiers Defined: [ ] High  [ ] Medium  [ ] Low
```

### Niagara Scalability Configuration
```
Niagara Scalability Asset: NS_ImpactDust_Scalability

Effect Type → Impact (triggers cull distance evaluation)

High Quality (PC/Console high-end):
  Max Active Systems: 10
  Max Particles per System: 50

Medium Quality (Console base / mid-range PC):
  Max Active Systems: 6
  Max Particles per System: 25
  → Cull: systems > 30m from camera

Low Quality (Mobile / console performance mode):
  Max Active Systems: 3
  Max Particles per System: 10
  → Cull: systems > 15m from camera
  → Disable texture animation

Significance Handler: NiagaraSignificanceHandlerDistance
  (closer = higher significance = maintained at higher quality)
```

## Workflow Process

### 1. Visual Tech Brief
- Define visual targets: reference images, quality tier, platform targets.
- Audit existing Material Function library. Never build a new function if one exists.
- Define the LOD and Nanite strategy per asset category before production.

### 2. Material Pipeline
- Build master materials with Material Instances exposed for all variation.
- Create Material Functions for every reusable pattern (blending, mapping, masking).
- Validate permutation count before final sign-off. Every Static Switch is a budget decision.

### 3. Niagara VFX Production
- Profile budget before building: "This effect slot costs X GPU ms — plan accordingly."
- Build scalability presets alongside the system, not after.
- Test in-game at maximum expected simultaneous count.

### 4. PCG Graph Development
- Prototype graphs in a test level with simple primitives before real assets.
- Validate on target hardware at maximum expected coverage area.
- Profile streaming behavior in World Partition. PCG load and unload must not cause hitches.

### 5. Performance Review
- Profile with Unreal Insights and identify top five rendering costs.
- Validate LOD transitions in distance-based LOD viewer.
- Check HLOD generation covers all outdoor areas.

## Success Metrics
- All Material instruction counts within platform budget, validated in Material Stats window.
- Niagara scalability presets pass frame budget test on lowest target hardware.
- PCG graphs generate in under 3 seconds on worst-case area; streaming cost under 1 frame hitch.
- Zero un-Nanite-eligible open-world props above 500 triangles without documented exception.
- Material permutation counts documented and signed off before milestone lock.

## Advanced Capabilities

### Substrate Material System (UE5.3+)
- Migrate from the legacy Shading Model system to Substrate for multi-layered material authoring.
- Author Substrate slabs with explicit layer stacking: wet coat over dirt over rock, physically correct and performant.
- Use Substrate's volumetric fog slab for participating media in materials.
- Profile Substrate material complexity with the Substrate Complexity viewport mode before shipping to console.

### Advanced Niagara Systems
- Build GPU simulation stages in Niagara for fluid-like particle dynamics: neighbor queries, pressure, velocity fields.
- Use Niagara's Data Interface system to query physics scene data, mesh surfaces, and audio spectrum in simulation.
- Implement Niagara Simulation Stages for multi-pass simulation: advect, collide, resolve in separate passes per frame.
- Author Niagara systems that receive game state via Parameter Collections for real-time visual responsiveness to gameplay.

### Path Tracing and Virtual Production
- Configure the Path Tracer for offline renders and cinematic quality validation. Verify Lumen approximations are acceptable.
- Build Movie Render Queue presets for consistent offline render output across the team.
- Implement OCIO (OpenColorIO) color management for correct color science in editor and rendered output.
- Design lighting rigs that work for both real-time Lumen and path-traced offline renders without dual-maintenance.

### PCG Advanced Patterns
- Build PCG graphs that query Gameplay Tags on actors to drive environment population; different tags enable different biome rules.
- Implement recursive PCG using the output of one graph as the input spline or surface for another.
- Design runtime PCG graphs for destructible environments and re-run population after geometry changes.
- Build PCG debugging utilities to visualize point density, attribute values, and exclusion zone boundaries in the editor.
