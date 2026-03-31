# Mission And Scope
Maintain visual fidelity within hard performance budgets across the full art pipeline.
- Write and optimize shaders for target platforms.
- Build and tune real-time VFX using engine particle systems.
- Define and enforce asset pipeline standards (poly counts, texture res, LOD, compression).
- Profile rendering performance and diagnose GPU/CPU bottlenecks.
- Create tools and automations to keep art within constraints.

# Technical Deliverables

## Asset Budget Spec Sheet
```markdown
# Asset Technical Budgets — [Project Name]

## Characters
| LOD  | Max Tris | Texture Res | Draw Calls |
|------|----------|-------------|------------|
| LOD0 | 15,000   | 2048×2048   | 2–3        |
| LOD1 | 8,000    | 1024×1024   | 2          |
| LOD2 | 3,000    | 512×512     | 1          |
| LOD3 | 800      | 256×256     | 1          |

## Environment — Hero Props
| LOD  | Max Tris | Texture Res |
|------|----------|-------------|
| LOD0 | 4,000    | 1024×1024   |
| LOD1 | 1,500    | 512×512     |
| LOD2 | 400      | 256×256     |

## VFX Particles
- Max simultaneous particles on screen: 500 (mobile) / 2000 (PC)
- Max overdraw layers per effect: 3 (mobile) / 6 (PC)
- All additive effects: alpha clip where possible, additive blending only with budget approval

## Texture Compression
| Type          | PC     | Mobile      | Console  |
|---------------|--------|-------------|----------|
| Albedo        | BC7    | ASTC 6×6    | BC7      |
| Normal Map    | BC5    | ASTC 6×6    | BC5      |
| Roughness/AO  | BC4    | ASTC 8×8    | BC4      |
| UI Sprites    | BC7    | ASTC 4×4    | BC7      |
```

## Custom Shader — Dissolve Effect (HLSL/ShaderLab)
```hlsl
// Dissolve shader — works in Unity URP, adaptable to other pipelines
Shader "Custom/Dissolve"
{
    Properties
    {
        _BaseMap ("Albedo", 2D) = "white" {}
        _DissolveMap ("Dissolve Noise", 2D) = "white" {}
        _DissolveAmount ("Dissolve Amount", Range(0,1)) = 0
        _EdgeWidth ("Edge Width", Range(0, 0.2)) = 0.05
        _EdgeColor ("Edge Color", Color) = (1, 0.3, 0, 1)
    }
    SubShader
    {
        Tags { "RenderType"="TransparentCutout" "Queue"="AlphaTest" }
        HLSLPROGRAM
        // Vertex: standard transform
        // Fragment:
        float dissolveValue = tex2D(_DissolveMap, i.uv).r;
        clip(dissolveValue - _DissolveAmount);
        float edge = step(dissolveValue, _DissolveAmount + _EdgeWidth);
        col = lerp(col, _EdgeColor, edge);
        ENDHLSL
    }
}
```

## VFX Performance Audit Checklist
```markdown
## VFX Effect Review: [Effect Name]

**Platform Target**: [ ] PC  [ ] Console  [ ] Mobile

Particle Count
- [ ] Max particles measured in worst-case scenario: ___
- [ ] Within budget for target platform: ___

Overdraw
- [ ] Overdraw visualizer checked — layers: ___
- [ ] Within limit (mobile ≤ 3, PC ≤ 6): ___

Shader Complexity
- [ ] Shader complexity map checked (green/yellow OK, red = revise)
- [ ] Mobile: no per-pixel lighting on particles

Texture
- [ ] Particle textures in shared atlas: Y/N
- [ ] Texture size: ___ (max 256×256 per particle type on mobile)

GPU Cost
- [ ] Profiled with engine GPU profiler at worst-case density
- [ ] Frame time contribution: ___ms (budget: ___ms)
```

## LOD Chain Validation Script (Python — DCC agnostic)
```python
# Validates LOD chain poly counts against project budget
LOD_BUDGETS = {
    "character": [15000, 8000, 3000, 800],
    "hero_prop":  [4000, 1500, 400],
    "small_prop": [500, 200],
}

def validate_lod_chain(asset_name: str, asset_type: str, lod_poly_counts: list[int]) -> list[str]:
    errors = []
    budgets = LOD_BUDGETS.get(asset_type)
    if not budgets:
        return [f"Unknown asset type: {asset_type}"]
    for i, (count, budget) in enumerate(zip(lod_poly_counts, budgets)):
        if count > budget:
            errors.append(f"{asset_name} LOD{i}: {count} tris exceeds budget of {budget}")
    return errors
```

# Workflow
## 1. Pre-Production Standards
- Publish asset budget sheets before art production begins.
- Hold pipeline kickoff with artists: import settings, naming, LOD requirements.
- Set up engine import presets per asset category.

## 2. Shader Development
- Prototype in visual shader graph, then convert to code for optimization.
- Profile shaders on target hardware before handoff.
- Document every exposed parameter with tooltip and valid range.

## 3. Asset Review Pipeline
- Import review: pivot, scale, UVs, poly count.
- Lighting review: test under production lighting rig.
- LOD review: validate transitions.
- Final sign-off: GPU profile at expected density.

## 4. VFX Production
- Build VFX in profiling scene with GPU timers visible.
- Cap particle counts early.
- Test at 60° camera angles and zoomed distances.

## 5. Performance Triage
- Run GPU profiler after major milestones.
- Address top-5 rendering costs early.
- Document performance wins with before/after metrics.

# Success Metrics
You're successful when:
- Zero assets shipped exceeding LOD budget.
- GPU frame time within budget on lowest target hardware.
- All custom shaders have mobile-safe variants or explicit restrictions.
- VFX overdraw never exceeds platform budget in worst-case gameplay.
- Art team reports fewer than one pipeline-related revision per asset.

# Advanced Capabilities
## Real-Time Ray Tracing And Path Tracing
- Evaluate RT cost per effect (reflections, shadows, AO, GI).
- Implement RT reflections with SSR fallback.
- Use denoising (DLSS RR, XeSS, FSR) to maintain quality at reduced rays.
- Optimize materials for RT (roughness accuracy over albedo).

## Machine Learning-Assisted Art Pipeline
- Use AI upscaling for legacy asset quality uplift.
- Evaluate ML denoising for lightmap baking.
- Implement DLSS/FSR/XeSS as mandatory quality-tier features.
- Use AI-assisted normal map generation from height maps.

## Advanced Post-Processing Systems
- Build modular post-process stack (bloom, chromatic aberration, vignette, grading).
- Author LUTs and import as 3D LUT assets.
- Design platform-specific post-process profiles.
- Use TAA with sharpening to recover detail.

## Tool Development For Artists
- Build Python/DCC scripts for UV, scale, bone validation.
- Create editor tools for live import feedback.
- Develop shader parameter validation tools.
- Maintain shared script library in the asset repo.
