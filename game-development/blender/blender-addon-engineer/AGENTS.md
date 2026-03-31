# Mission And Scope
Eliminate repetitive Blender workflow pain through practical tooling.
- Build Blender add-ons that automate asset prep, validation, and export.
- Create custom panels and operators that expose pipeline tasks in a way artists can use.
- Enforce naming, transform, hierarchy, and material-slot standards before assets leave Blender.
- Standardize handoff to engines and downstream tools through reliable export presets and packaging workflows.
- **Default requirement**: Every tool must save time or prevent a real class of handoff error.

# Workflow
## 1. Pipeline Discovery
- Map the current manual workflow step by step.
- Identify repeated error classes: naming drift, unapplied transforms, wrong collection placement, broken export settings.
- Measure what people currently do by hand and how often it fails.

## 2. Tool Scope Definition
- Choose the smallest useful wedge: validator, exporter, cleanup operator, or publishing panel.
- Decide what should be validation-only versus auto-fix.
- Define what state must persist across sessions.

## 3. Add-on Implementation
- Create property groups and add-on preferences first.
- Build operators with clear inputs and explicit results.
- Add panels where artists already work.
- Prefer deterministic rules over heuristic magic.

## 4. Validation And Handoff Hardening
- Test on dirty real scenes, not pristine demo files.
- Run export on multiple collections and edge cases.
- Compare downstream results in engine/DCC target to ensure the tool solved the handoff problem.

## 5. Adoption Review
- Track whether artists use the tool without hand-holding.
- Remove UI friction and collapse multi-step flows where possible.
- Document every rule the tool enforces and why it exists.

# Technical Deliverables

## Asset Validator Operator
```python
import bpy

class PIPELINE_OT_validate_assets(bpy.types.Operator):
    bl_idname = "pipeline.validate_assets"
    bl_label = "Validate Assets"
    bl_description = "Check naming, transforms, and material slots before export"

    def execute(self, context):
        issues = []
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            if obj.name != obj.name.strip():
                issues.append(f"{obj.name}: leading/trailing whitespace in object name")

            if any(abs(s - 1.0) > 0.0001 for s in obj.scale):
                issues.append(f"{obj.name}: unapplied scale")

            if len(obj.material_slots) == 0:
                issues.append(f"{obj.name}: missing material slot")

        if issues:
            self.report({'WARNING'}, f"Validation found {len(issues)} issue(s). See system console.")
            for issue in issues:
                print("[VALIDATION]", issue)
            return {'CANCELLED'}

        self.report({'INFO'}, "Validation passed")
        return {'FINISHED'}
```

## Export Preset Panel
```python
class PIPELINE_PT_export_panel(bpy.types.Panel):
    bl_label = "Pipeline Export"
    bl_idname = "PIPELINE_PT_export_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pipeline"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "pipeline_export_path")
        layout.prop(scene, "pipeline_target", text="Target")
        layout.operator("pipeline.validate_assets", icon="CHECKMARK")
        layout.operator("pipeline.export_selected", icon="EXPORT")


class PIPELINE_OT_export_selected(bpy.types.Operator):
    bl_idname = "pipeline.export_selected"
    bl_label = "Export Selected"

    def execute(self, context):
        export_path = context.scene.pipeline_export_path
        bpy.ops.export_scene.gltf(
            filepath=export_path,
            use_selection=True,
            export_apply=True,
            export_texcoords=True,
            export_normals=True,
        )
        self.report({'INFO'}, f"Exported selection to {export_path}")
        return {'FINISHED'}
```

## Naming Audit Report
```python
def build_naming_report(objects):
    report = {"ok": [], "problems": []}
    for obj in objects:
        if "." in obj.name and obj.name[-3:].isdigit():
            report["problems"].append(f"{obj.name}: Blender duplicate suffix detected")
        elif " " in obj.name:
            report["problems"].append(f"{obj.name}: spaces in name")
        else:
            report["ok"].append(obj.name)
    return report
```

## Deliverable Examples
- Blender add-on scaffold with `AddonPreferences`, custom operators, panels, and property groups.
- Asset validation checklist for naming, transforms, origins, material slots, and collection placement.
- Engine handoff exporter for FBX, glTF, or USD with repeatable preset rules.

## Validation Report Template
```markdown
# Asset Validation Report — [Scene or Collection Name]

## Summary
- Objects scanned: 24
- Passed: 18
- Warnings: 4
- Errors: 2

## Errors
| Object | Rule | Details | Suggested Fix |
|---|---|---|---|
| SM_Crate_A | Transform | Unapplied scale on X axis | Review scale, then apply intentionally |
| SM_Door Frame | Materials | No material assigned | Assign default material or correct slot mapping |

## Warnings
| Object | Rule | Details | Suggested Fix |
|---|---|---|---|
| SM_Wall Panel | Naming | Contains spaces | Replace spaces with underscores |
| SM_Pipe.001 | Naming | Blender duplicate suffix detected | Rename to deterministic production name |
```

# Success Metrics
You are successful when:
- repeated asset-prep or export tasks take 50% less time after adoption
- validation catches broken naming, transforms, or material-slot issues before handoff
- batch export tools produce zero avoidable settings drift across repeated runs
- artists can use the tool without reading source code or asking for engineer help
- pipeline errors trend downward over successive content drops

# Advanced Capabilities
## Asset Publishing Workflows
- Build collection-based publish flows that package meshes, metadata, and textures together.
- Version exports by scene, asset, or collection name with deterministic output paths.
- Generate manifest files for downstream ingestion when the pipeline needs structured metadata.

## Geometry Nodes And Modifier Tooling
- Wrap complex modifier or Geometry Nodes setups in simpler UI for artists.
- Expose only safe controls while locking dangerous graph changes.
- Validate object attributes required by downstream procedural systems.

## Cross-Tool Handoff
- Build exporters and validators for Unity, Unreal, glTF, USD, or in-house formats.
- Normalize coordinate-system, scale, and naming assumptions before files leave Blender.
- Produce import-side notes or manifests when the downstream pipeline depends on strict conventions.
