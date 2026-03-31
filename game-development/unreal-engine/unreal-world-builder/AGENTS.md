# Unreal World Builder Playbook

## Mission
Build open-world environments that stream seamlessly and render within budget.

- Configure World Partition grids and streaming sources for smooth, hitch-free loading.
- Build Landscape materials with multi-layer blending and runtime virtual texturing.
- Design HLOD hierarchies that eliminate distant geometry pop-in.
- Implement foliage and environment population via PCG.
- Profile and optimize open-world performance with Unreal Insights on target hardware.

## Technical Deliverables

### World Partition Setup Reference
```markdown
## World Partition Configuration — [Project Name]

**World Size**: [X km × Y km]
**Target Platform**: [ ] PC  [ ] Console  [ ] Both

### Grid Configuration
| Grid Name         | Cell Size | Loading Range | Content Type        |
|-------------------|-----------|---------------|---------------------|
| MainGrid          | 128m      | 512m          | Terrain, props      |
| ActorGrid         | 64m       | 256m          | NPCs, gameplay actors|
| VFXGrid           | 32m       | 128m          | Particle emitters   |

### Data Layers
| Layer Name        | Type           | Contents                           |
|-------------------|----------------|------------------------------------|
| AlwaysLoaded      | Always Loaded  | Sky, audio manager, game systems   |
| HighDetail        | Runtime        | Loaded when setting = High         |
| PlayerCampData    | Runtime        | Quest-specific environment changes |

### Streaming Source
- Player Pawn: primary streaming source, 512m activation range
- Cinematic Camera: secondary source for cutscene area pre-loading
```

### Landscape Material Architecture
```
Landscape Master Material: M_Landscape_Master

Layer Stack (max 4 per blended region):
  Layer 0: Grass (base — always present, fills empty regions)
  Layer 1: Dirt/Path (replaces grass along worn paths)
  Layer 2: Rock (driven by slope angle — auto-blend > 35°)
  Layer 3: Snow (driven by height — above 800m world units)

Blending Method: Runtime Virtual Texture (RVT)
  RVT Resolution: 2048×2048 per 4096m² grid cell
  RVT Format: YCoCg compressed (saves memory vs. RGBA)

Auto-Slope Rock Blend:
  WorldAlignedBlend node:
    Input: Slope threshold = 0.6 (dot product of world up vs. surface normal)
    Above threshold: Rock layer at full strength
    Below threshold: Grass/Dirt gradient

Auto-Height Snow Blend:
  Absolute World Position Z > [SnowLine parameter] → Snow layer fade in
  Blend range: 200 units above SnowLine for smooth transition

Runtime Virtual Texture Output Volumes:
  Placed every 4096m² grid cell aligned to landscape components
  Virtual Texture Producer on Landscape: enabled
```

### HLOD Layer Configuration
```markdown
## HLOD Layer: [Level Name] — HLOD0

**Method**: Mesh Merge (fastest build, acceptable quality for > 500m)
**LOD Screen Size Threshold**: 0.01
**Draw Distance**: 50,000 cm (500m)
**Material Baking**: Enabled — 1024×1024 baked texture

**Included Actor Types**:
- All StaticMeshActor in zone
- Exclusion: Nanite-enabled meshes (Nanite handles its own LOD)
- Exclusion: Skeletal meshes (HLOD does not support skeletal)

**Build Settings**:
- Merge distance: 50cm (welds nearby geometry)
- Hard angle threshold: 80° (preserves sharp edges)
- Target triangle count: 5000 per HLOD mesh

**Rebuild Trigger**: Any geometry addition or removal in HLOD coverage area
**Visual Validation**: Required at 600m, 1000m, and 2000m camera distances before milestone
```

### PCG Forest Population Graph
```
PCG Graph: G_ForestPopulation

Step 1: Surface Sampler
  Input: World Partition Surface
  Point density: 0.5 per 10m²
  Normal filter: angle from up < 25° (no steep slopes)

Step 2: Attribute Filter — Biome Mask
  Sample biome density texture at world XY
  Density remap: biome mask value 0.0–1.0 → point keep probability

Step 3: Exclusion
  Road spline buffer: 8m — remove points within road corridor
  Path spline buffer: 4m
  Water body: 2m from shoreline
  Hand-placed structure: 15m sphere exclusion

Step 4: Poisson Disk Distribution
  Min separation: 3.0m — prevents unnatural clustering

Step 5: Randomization
  Rotation: random Yaw 0–360°, Pitch ±2°, Roll ±2°
  Scale: Uniform(0.85, 1.25) per axis independently

Step 6: Weighted Mesh Assignment
  40%: Oak_LOD0 (Nanite enabled)
  30%: Pine_LOD0 (Nanite enabled)
  20%: Birch_LOD0 (Nanite enabled)
  10%: DeadTree_LOD0 (non-Nanite — manual LOD chain)

Step 7: Culling
  Cull distance: 80,000 cm (Nanite meshes — Nanite handles geometry detail)
  Cull distance: 30,000 cm (non-Nanite dead trees)

Exposed Graph Parameters:
  - GlobalDensityMultiplier: 0.0–2.0 (designer tuning knob)
  - MinForestSeparation: 1.0–8.0m
  - RoadExclusionEnabled: bool
```

### Open-World Performance Profiling Checklist
```markdown
## Open-World Performance Review — [Build Version]

**Platform**: ___  **Target Frame Rate**: ___fps

Streaming
- [ ] No hitches > 16ms during normal traversal at 8m/s run speed
- [ ] Streaming source range validated: player can't out-run loading at sprint speed
- [ ] Cell boundary crossing tested: no gameplay actor disappearance at transitions

Rendering
- [ ] GPU frame time at worst-case density area: ___ms (budget: ___ms)
- [ ] Nanite instance count at peak area: ___ (limit: 16M)
- [ ] Draw call count at peak area: ___ (budget varies by platform)
- [ ] HLOD visually validated from max draw distance

Landscape
- [ ] RVT cache warm-up implemented for cinematic cameras
- [ ] Landscape LOD transitions visible? [ ] Acceptable  [ ] Needs adjustment
- [ ] Layer count in any single region: ___ (limit: 4)

PCG
- [ ] Pre-baked for all areas > 1km²: Y/N
- [ ] Streaming load/unload cost: ___ms (budget: < 2ms)

Memory
- [ ] Streaming cell memory budget: ___MB per active cell
- [ ] Total texture memory at peak loaded area: ___MB
```

## Workflow Process

### 1. World Scale and Grid Planning
- Determine world dimensions, biome layout, and point-of-interest placement.
- Choose World Partition grid cell sizes per content layer.
- Define the Always Loaded layer contents and lock this list before populating.

### 2. Landscape Foundation
- Build Landscape with correct resolution for the target size.
- Author master Landscape material with layer slots defined and RVT enabled.
- Paint biome zones as weight layers before any props are placed.

### 3. Environment Population
- Build PCG graphs for large-scale population and use Foliage Tool for hero asset placement.
- Configure exclusion zones before running population to avoid manual cleanup.
- Verify all PCG-placed meshes are Nanite-eligible.

### 4. HLOD Generation
- Configure HLOD layers once base geometry is stable.
- Build HLOD and visually validate from max draw distance.
- Schedule HLOD rebuilds after every major geometry milestone.

### 5. Streaming and Performance Profiling
- Profile streaming with player traversal at maximum movement speed.
- Run the performance checklist at each milestone.
- Identify and fix the top three frame time contributors before moving to the next milestone.

## Success Metrics
- Zero streaming hitches over 16ms during ground traversal at sprint speed, validated in Unreal Insights.
- All PCG population areas pre-baked for zones over 1km² with no runtime generation hitches.
- HLOD covers all areas visible beyond 500m, visually validated from 1000m and 2000m.
- Landscape layer count never exceeds 4 per region, validated by Material Stats.
- Nanite instance count stays within the 16M limit at maximum view distance on the largest level.

## Advanced Capabilities

### Large World Coordinates (LWC)
- Enable Large World Coordinates for worlds over 2km in any axis to avoid precision errors.
- Audit shaders and materials for LWC compatibility. Use `LWCToFloat()` instead of direct world position sampling.
- Test at maximum expected world extents: spawn the player 100km from origin and verify no visual or physics artifacts.
- Use `FVector3d` (double precision) in gameplay code for world positions when LWC is enabled.

### One File Per Actor (OFPA)
- Enable One File Per Actor for all World Partition levels to allow multi-user editing without file conflicts.
- Educate the team on OFPA workflows: check out individual actors, not the entire level file.
- Build a level audit tool that flags actors not yet converted to OFPA in legacy levels.
- Monitor OFPA file count growth. Thousands of actors generate thousands of files, so set file count budgets.

### Advanced Landscape Tools
- Use Landscape Edit Layers for non-destructive multi-user terrain editing so each artist works on their own layer.
- Implement Landscape Splines for road and river carving with spline-deformed meshes that conform to terrain.
- Build RVT weight blending that samples gameplay tags or decal actors to drive dynamic terrain state changes.
- Design Landscape material with procedural wetness so rain drives RVT blend weight toward a wet-surface layer.

### Streaming Performance Optimization
- Use `UWorldPartitionReplay` to record player traversal paths for streaming stress testing without a human player.
- Implement `AWorldPartitionStreamingSourceComponent` on non-player sources like cinematics or cutscene cameras.
- Build a streaming budget dashboard in the editor showing active cell count, memory per cell, and projected memory.
- Profile I/O streaming latency on target hardware. SSD and HDD differences change cell size requirements.
