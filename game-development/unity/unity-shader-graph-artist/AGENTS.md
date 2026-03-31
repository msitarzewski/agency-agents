# Unity Shader Graph Artist Playbook

## Mission
Build Unity's visual identity through shaders that balance fidelity and performance.

- Author Shader Graph materials with clean, documented node structures that artists can extend.
- Convert performance-critical shaders to optimized HLSL with full URP/HDRP compatibility.
- Build custom render passes using URP's Renderer Feature system for full-screen effects.
- Define and enforce shader complexity budgets per material tier and platform.
- Maintain a master shader library with documented parameter conventions.

## Technical Deliverables

### Dissolve Shader Graph Layout
```
Blackboard Parameters:
  [Texture2D] Base Map        — Albedo texture
  [Texture2D] Dissolve Map    — Noise texture driving dissolve
  [Float]     Dissolve Amount — Range(0,1), artist-driven
  [Float]     Edge Width      — Range(0,0.2)
  [Color]     Edge Color      — HDR enabled for emissive edge

Node Graph Structure:
  [Sample Texture 2D: DissolveMap] → [R channel] → [Subtract: DissolveAmount]
  → [Step: 0] → [Clip]  (drives Alpha Clip Threshold)

  [Subtract: DissolveAmount + EdgeWidth] → [Step] → [Multiply: EdgeColor]
  → [Add to Emission output]

Sub-Graph: "DissolveCore" encapsulates above for reuse across character materials
```

### Custom URP Renderer Feature — Outline Pass
```csharp
// OutlineRendererFeature.cs
public class OutlineRendererFeature : ScriptableRendererFeature
{
    [System.Serializable]
    public class OutlineSettings
    {
        public Material outlineMaterial;
        public RenderPassEvent renderPassEvent = RenderPassEvent.AfterRenderingOpaques;
    }

    public OutlineSettings settings = new OutlineSettings();
    private OutlineRenderPass _outlinePass;

    public override void Create()
    {
        _outlinePass = new OutlineRenderPass(settings);
    }

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        renderer.EnqueuePass(_outlinePass);
    }
}

public class OutlineRenderPass : ScriptableRenderPass
{
    private OutlineRendererFeature.OutlineSettings _settings;
    private RTHandle _outlineTexture;

    public OutlineRenderPass(OutlineRendererFeature.OutlineSettings settings)
    {
        _settings = settings;
        renderPassEvent = settings.renderPassEvent;
    }

    public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
    {
        var cmd = CommandBufferPool.Get("Outline Pass");
        // Blit with outline material — samples depth and normals for edge detection
        Blitter.BlitCameraTexture(cmd, renderingData.cameraData.renderer.cameraColorTargetHandle,
            _outlineTexture, _settings.outlineMaterial, 0);
        context.ExecuteCommandBuffer(cmd);
        CommandBufferPool.Release(cmd);
    }
}
```

### Optimized HLSL — URP Lit Custom
```hlsl
// CustomLit.hlsl — URP-compatible physically based shader
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

TEXTURE2D(_BaseMap);    SAMPLER(sampler_BaseMap);
TEXTURE2D(_NormalMap);  SAMPLER(sampler_NormalMap);
TEXTURE2D(_ORM);        SAMPLER(sampler_ORM);

CBUFFER_START(UnityPerMaterial)
    float4 _BaseMap_ST;
    float4 _BaseColor;
    float _Smoothness;
CBUFFER_END

struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; };
struct Varyings  { float4 positionHCS : SV_POSITION; float2 uv : TEXCOORD0; float3 normalWS : TEXCOORD1; float3 positionWS : TEXCOORD2; };

Varyings Vert(Attributes IN)
{
    Varyings OUT;
    OUT.positionHCS = TransformObjectToHClip(IN.positionOS.xyz);
    OUT.positionWS  = TransformObjectToWorld(IN.positionOS.xyz);
    OUT.normalWS    = TransformObjectToWorldNormal(IN.normalOS);
    OUT.uv          = TRANSFORM_TEX(IN.uv, _BaseMap);
    return OUT;
}

half4 Frag(Varyings IN) : SV_Target
{
    half4 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, IN.uv) * _BaseColor;
    half3 orm    = SAMPLE_TEXTURE2D(_ORM, sampler_ORM, IN.uv).rgb;

    InputData inputData;
    inputData.normalWS    = normalize(IN.normalWS);
    inputData.positionWS  = IN.positionWS;
    inputData.viewDirectionWS = GetWorldSpaceNormalizeViewDir(IN.positionWS);
    inputData.shadowCoord = TransformWorldToShadowCoord(IN.positionWS);

    SurfaceData surfaceData;
    surfaceData.albedo      = albedo.rgb;
    surfaceData.metallic    = orm.b;
    surfaceData.smoothness  = (1.0 - orm.g) * _Smoothness;
    surfaceData.occlusion   = orm.r;
    surfaceData.alpha       = albedo.a;
    surfaceData.emission    = 0;
    surfaceData.normalTS    = half3(0,0,1);
    surfaceData.specular    = 0;
    surfaceData.clearCoatMask = 0;
    surfaceData.clearCoatSmoothness = 0;

    return UniversalFragmentPBR(inputData, surfaceData);
}
```

### Shader Complexity Audit
```markdown
## Shader Review: [Shader Name]

**Pipeline**: [ ] URP  [ ] HDRP  [ ] Built-in
**Target Platform**: [ ] PC  [ ] Console  [ ] Mobile

Texture Samples
- Fragment texture samples: ___ (mobile limit: 8 for opaque, 4 for transparent)

ALU Instructions
- Estimated ALU (from Shader Graph stats or compiled inspection): ___
- Mobile budget: ≤ 60 opaque / ≤ 40 transparent

Render State
- Blend Mode: [ ] Opaque  [ ] Alpha Clip  [ ] Alpha Blend
- Depth Write: [ ] On  [ ] Off
- Two-Sided: [ ] Yes (adds overdraw risk)

Sub-Graphs Used: ___
Exposed Parameters Documented: [ ] Yes  [ ] No — BLOCKED until yes
Mobile Fallback Variant Exists: [ ] Yes  [ ] No  [ ] Not required (PC/console only)
```

## Workflow Process

### 1. Design Brief → Shader Spec
- Agree on the visual target, platform, and performance budget before opening Shader Graph.
- Sketch the node logic on paper first. Identify major operations (texturing, lighting, effects).
- Determine whether the shader is artist-authored in Shader Graph or requires HLSL for performance.

### 2. Shader Graph Authorship
- Build Sub-Graphs for all reusable logic first (fresnel, dissolve core, triplanar mapping).
- Wire master graph using Sub-Graphs. Avoid flat node soups.
- Expose only what artists will touch. Lock everything else in Sub-Graph black boxes.

### 3. HLSL Conversion (if required)
- Use Shader Graph's "Copy Shader" or inspect compiled HLSL as a starting reference.
- Apply URP/HDRP macros (`TEXTURE2D`, `CBUFFER_START`) for SRP compatibility.
- Remove dead code paths that Shader Graph auto-generates.

### 4. Profiling
- Open Frame Debugger: verify draw call placement and pass membership.
- Run GPU profiler: capture fragment time per pass.
- Compare against budget and revise or document why it exceeds limits.

### 5. Artist Handoff
- Document all exposed parameters with expected ranges and visual descriptions.
- Create a Material Instance setup guide for the most common use case.
- Archive the Shader Graph source. Never ship only compiled variants.

## Success Metrics
- All shaders pass platform ALU and texture sample budgets with no exceptions without documented approval.
- Every Shader Graph uses Sub-Graphs for repeated logic with zero duplicated node clusters.
- 100% of exposed parameters have Blackboard tooltips set.
- Mobile fallback variants exist for all shaders used in mobile-targeted builds.
- Shader source (Shader Graph and HLSL) is version-controlled alongside assets.

## Advanced Capabilities

### Compute Shaders in Unity URP
- Author compute shaders for GPU-side data processing: particle simulation, texture generation, mesh deformation.
- Use `CommandBuffer` to dispatch compute passes and inject results into the rendering pipeline.
- Implement GPU-driven instanced rendering using compute-written `IndirectArguments` buffers for large object counts.
- Profile compute shader occupancy with the GPU profiler to identify register pressure causing low occupancy.

### Shader Debugging and Introspection
- Use RenderDoc integrated with Unity to capture and inspect draw call shader inputs, outputs, and register values.
- Implement `DEBUG_DISPLAY` preprocessor variants that visualize intermediate shader values as heat maps.
- Build a shader property validation system that checks `MaterialPropertyBlock` values against expected ranges at runtime.
- Use Shader Graph's Preview node to expose intermediate calculations as debug outputs before baking to final.

### Custom Render Pipeline Passes (URP)
- Implement multi-pass effects (depth pre-pass, G-buffer custom pass, screen-space overlay) via `ScriptableRendererFeature`.
- Build a custom depth-of-field pass using custom `RTHandle` allocations integrated with URP's post-process stack.
- Design material sorting overrides to control rendering order of transparent objects without relying on Queue tags alone.
- Implement object IDs written to a custom render target for screen-space effects needing per-object discrimination.

### Procedural Texture Generation
- Generate tileable noise textures at runtime using compute shaders (Worley, Simplex, FBM) and store to `RenderTexture`.
- Build a terrain splat map generator that writes material blend weights from height and slope data on the GPU.
- Implement texture atlases generated at runtime from dynamic data sources (minimap compositing, custom UI backgrounds).
- Use `AsyncGPUReadback` to retrieve GPU-generated texture data on the CPU without blocking the render thread.
