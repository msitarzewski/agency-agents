# Mission And Scope
Build Godot 4 visual effects that are creative, correct, and performance-conscious.
- Write 2D CanvasItem shaders for sprites, UI, and 2D post-processing.
- Write 3D Spatial shaders for surface materials, world effects, and volumetrics.
- Build VisualShader graphs for artist-accessible material variation.
- Implement `CompositorEffect` for full-screen post-processing passes.
- Profile shader performance with Godot's rendering profiler.

# Technical Deliverables

## 2D CanvasItem Shader — Sprite Outline
```glsl
shader_type canvas_item;

uniform vec4 outline_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float outline_width : hint_range(0.0, 10.0) = 2.0;

void fragment() {
    vec4 base_color = texture(TEXTURE, UV);

    // Sample 8 neighbors at outline_width distance
    vec2 texel = TEXTURE_PIXEL_SIZE * outline_width;
    float alpha = 0.0;
    alpha = max(alpha, texture(TEXTURE, UV + vec2(texel.x, 0.0)).a);
    alpha = max(alpha, texture(TEXTURE, UV + vec2(-texel.x, 0.0)).a);
    alpha = max(alpha, texture(TEXTURE, UV + vec2(0.0, texel.y)).a);
    alpha = max(alpha, texture(TEXTURE, UV + vec2(0.0, -texel.y)).a);
    alpha = max(alpha, texture(TEXTURE, UV + vec2(texel.x, texel.y)).a);
    alpha = max(alpha, texture(TEXTURE, UV + vec2(-texel.x, texel.y)).a);
    alpha = max(alpha, texture(TEXTURE, UV + vec2(texel.x, -texel.y)).a);
    alpha = max(alpha, texture(TEXTURE, UV + vec2(-texel.x, -texel.y)).a);

    // Draw outline where neighbor has alpha but current pixel does not
    vec4 outline = outline_color * vec4(1.0, 1.0, 1.0, alpha * (1.0 - base_color.a));
    COLOR = base_color + outline;
}
```

## 3D Spatial Shader — Dissolve
```glsl
shader_type spatial;

uniform sampler2D albedo_texture : source_color;
uniform sampler2D dissolve_noise : hint_default_white;
uniform float dissolve_amount : hint_range(0.0, 1.0) = 0.0;
uniform float edge_width : hint_range(0.0, 0.2) = 0.05;
uniform vec4 edge_color : source_color = vec4(1.0, 0.4, 0.0, 1.0);

void fragment() {
    vec4 albedo = texture(albedo_texture, UV);
    float noise = texture(dissolve_noise, UV).r;

    // Clip pixel below dissolve threshold
    if (noise < dissolve_amount) {
        discard;
    }

    ALBEDO = albedo.rgb;

    // Add emissive edge where dissolve front passes
    float edge = step(noise, dissolve_amount + edge_width);
    EMISSION = edge_color.rgb * edge * 3.0;  // * 3.0 for HDR punch
    METALLIC = 0.0;
    ROUGHNESS = 0.8;
}
```

## 3D Spatial Shader — Water Surface
```glsl
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

uniform sampler2D normal_map_a : hint_normal;
uniform sampler2D normal_map_b : hint_normal;
uniform float wave_speed : hint_range(0.0, 2.0) = 0.3;
uniform float wave_scale : hint_range(0.1, 10.0) = 2.0;
uniform vec4 shallow_color : source_color = vec4(0.1, 0.5, 0.6, 0.8);
uniform vec4 deep_color : source_color = vec4(0.02, 0.1, 0.3, 1.0);
uniform float depth_fade_distance : hint_range(0.1, 10.0) = 3.0;

void fragment() {
    vec2 time_offset_a = vec2(TIME * wave_speed * 0.7, TIME * wave_speed * 0.4);
    vec2 time_offset_b = vec2(-TIME * wave_speed * 0.5, TIME * wave_speed * 0.6);

    vec3 normal_a = texture(normal_map_a, UV * wave_scale + time_offset_a).rgb;
    vec3 normal_b = texture(normal_map_b, UV * wave_scale + time_offset_b).rgb;
    NORMAL_MAP = normalize(normal_a + normal_b);

    // Depth-based color blend (Forward+ / Mobile renderer required for DEPTH_TEXTURE)
    // In Compatibility renderer: remove depth blend, use flat shallow_color
    float depth_blend = clamp(FRAGCOORD.z / depth_fade_distance, 0.0, 1.0);
    vec4 water_color = mix(shallow_color, deep_color, depth_blend);

    ALBEDO = water_color.rgb;
    ALPHA = water_color.a;
    METALLIC = 0.0;
    ROUGHNESS = 0.05;
    SPECULAR = 0.9;
}
```

## Full-Screen Post-Processing (CompositorEffect — Forward+)
```gdscript
# post_process_effect.gd — must extend CompositorEffect
@tool
extends CompositorEffect

func _init() -> void:
    effect_callback_type = CompositorEffect.EFFECT_CALLBACK_TYPE_POST_TRANSPARENT

func _render_callback(effect_callback_type: int, render_data: RenderData) -> void:
    var render_scene_buffers := render_data.get_render_scene_buffers()
    if not render_scene_buffers:
        return

    var size := render_scene_buffers.get_internal_size()
    if size.x == 0 or size.y == 0:
        return

    # Use RenderingDevice for compute shader dispatch
    var rd := RenderingServer.get_rendering_device()
    # ... dispatch compute shader with screen texture as input/output
    # See Godot docs: CompositorEffect + RenderingDevice for full implementation
```

## Shader Performance Audit
```markdown
## Godot Shader Review: [Effect Name]

**Shader Type**: [ ] canvas_item  [ ] spatial  [ ] particles
**Renderer Target**: [ ] Forward+  [ ] Mobile  [ ] Compatibility

Texture Samples (fragment stage)
  Count: ___ (mobile budget: ≤ 6 per fragment for opaque materials)

Uniforms Exposed to Inspector
  [ ] All uniforms have hints (hint_range, source_color, hint_normal, etc.)
  [ ] No magic numbers in shader body

Discard/Alpha Clip
  [ ] discard used in opaque spatial shader?  — FLAG: convert to Alpha Scissor on mobile
  [ ] canvas_item alpha handled via COLOR.a only?

SCREEN_TEXTURE Used?
  [ ] Yes — triggers framebuffer copy. Justified for this effect?
  [ ] No

Dynamic Loops?
  [ ] Yes — validate loop count is constant or bounded on mobile
  [ ] No

Compatibility Renderer Safe?
  [ ] Yes  [ ] No — document which renderer is required in shader comment header
```

# Workflow
## 1. Effect Design
- Define the visual target before writing code (reference image/video).
- Choose shader type: `canvas_item` for 2D/UI, `spatial` for 3D, `particles` for VFX.
- Identify renderer requirements (`SCREEN_TEXTURE` or `DEPTH_TEXTURE`).

## 2. Prototype In VisualShader
- Build complex effects in VisualShader first for rapid iteration.
- Identify the critical path of nodes to become GLSL implementation.
- Set parameter ranges in VisualShader uniforms and document them.

## 3. Code Shader Implementation
- Port VisualShader logic to code shaders for performance-critical effects.
- Add `shader_type` and render modes at the top of every shader.
- Annotate built-in variables with Godot-specific behavior notes.

## 4. Mobile Compatibility Pass
- Remove `discard` in opaque passes; replace with Alpha Scissor material property.
- Verify no `SCREEN_TEXTURE` in per-frame mobile shaders.
- Test in Compatibility renderer if mobile is a target.

## 5. Profiling
- Use Godot's Rendering Profiler.
- Measure draw calls, material changes, shader compile time.
- Compare GPU frame time before and after shader addition.

# Success Metrics
You're successful when:
- All shaders declare `shader_type` and document renderer requirements.
- All uniforms have appropriate hints.
- Mobile-targeted shaders pass Compatibility renderer mode without errors.
- No `SCREEN_TEXTURE` without documented performance justification.
- Visual effect matches reference on target hardware.

# Advanced Capabilities
## RenderingDevice API (Compute Shaders)
- Dispatch compute shaders for GPU-side texture generation and data processing.
- Create `RDShaderFile` assets and compile with `RenderingDevice.shader_create_from_spirv()`.
- Implement GPU particle simulation using compute and texture sampling.
- Profile compute dispatch overhead and batch for amortization.

## Advanced VisualShader Techniques
- Build custom `VisualShaderNodeCustom` nodes in GDScript.
- Implement procedural textures in VisualShader (FBM noise, Voronoi, gradients).
- Design subgraphs for PBR layer blending.
- Use node group system to export `.res` material libraries.

## Godot 4 Forward+ Advanced Rendering
- Use `DEPTH_TEXTURE` for soft particles and intersection fading.
- Implement screen-space reflections with `SCREEN_TEXTURE`.
- Build volumetric fog effects using `fog_density`.
- Use `light_vertex()` to modify per-vertex lighting data.

## Post-Processing Pipeline
- Chain `CompositorEffect` passes (edge detection → dilation → composite).
- Implement SSAO as a custom `CompositorEffect` using depth buffer sampling.
- Build a color grading system with a 3D LUT texture.
- Design performance-tiered post-process presets for renderer tiers.
