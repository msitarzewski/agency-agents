# Unity Editor Tool Developer Playbook

## Mission
Reduce manual work and prevent errors through Unity Editor automation.

- Build `EditorWindow` tools that give teams insight into project state without leaving Unity.
- Author `PropertyDrawer` and `CustomEditor` extensions that make `Inspector` data clearer and safer to edit.
- Implement `AssetPostprocessor` rules that enforce naming conventions, import settings, and budget validation on every import.
- Create `MenuItem` and `ContextMenu` shortcuts for repeated manual operations.
- Write validation pipelines that run on build, catching errors before they reach a QA environment.

## Technical Deliverables

### Custom EditorWindow — Asset Auditor
```csharp
public class AssetAuditWindow : EditorWindow
{
    [MenuItem("Tools/Asset Auditor")]
    public static void ShowWindow() => GetWindow<AssetAuditWindow>("Asset Auditor");

    private Vector2 _scrollPos;
    private List<string> _oversizedTextures = new();
    private bool _hasRun = false;

    private void OnGUI()
    {
        GUILayout.Label("Texture Budget Auditor", EditorStyles.boldLabel);

        if (GUILayout.Button("Scan Project Textures"))
        {
            _oversizedTextures.Clear();
            ScanTextures();
            _hasRun = true;
        }

        if (_hasRun)
        {
            EditorGUILayout.HelpBox($"{_oversizedTextures.Count} textures exceed budget.", MessageWarningType());
            _scrollPos = EditorGUILayout.BeginScrollView(_scrollPos);
            foreach (var path in _oversizedTextures)
            {
                EditorGUILayout.BeginHorizontal();
                EditorGUILayout.LabelField(path, EditorStyles.miniLabel);
                if (GUILayout.Button("Select", GUILayout.Width(55)))
                    Selection.activeObject = AssetDatabase.LoadAssetAtPath<Texture>(path);
                EditorGUILayout.EndHorizontal();
            }
            EditorGUILayout.EndScrollView();
        }
    }

    private void ScanTextures()
    {
        var guids = AssetDatabase.FindAssets("t:Texture2D");
        int processed = 0;
        foreach (var guid in guids)
        {
            var path = AssetDatabase.GUIDToAssetPath(guid);
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer != null && importer.maxTextureSize > 1024)
                _oversizedTextures.Add(path);
            EditorUtility.DisplayProgressBar("Scanning...", path, (float)processed++ / guids.Length);
        }
        EditorUtility.ClearProgressBar();
    }

    private MessageType MessageWarningType() =>
        _oversizedTextures.Count == 0 ? MessageType.Info : MessageType.Warning;
}
```

### AssetPostprocessor — Texture Import Enforcer
```csharp
public class TextureImportEnforcer : AssetPostprocessor
{
    private const int MAX_RESOLUTION = 2048;
    private const string NORMAL_SUFFIX = "_N";
    private const string UI_PATH = "Assets/UI/";

    void OnPreprocessTexture()
    {
        var importer = (TextureImporter)assetImporter;
        string path = assetPath;

        // Enforce normal map type by naming convention
        if (System.IO.Path.GetFileNameWithoutExtension(path).EndsWith(NORMAL_SUFFIX))
        {
            if (importer.textureType != TextureImporterType.NormalMap)
            {
                importer.textureType = TextureImporterType.NormalMap;
                Debug.LogWarning($"[TextureImporter] Set '{path}' to Normal Map based on '_N' suffix.");
            }
        }

        // Enforce max resolution budget
        if (importer.maxTextureSize > MAX_RESOLUTION)
        {
            importer.maxTextureSize = MAX_RESOLUTION;
            Debug.LogWarning($"[TextureImporter] Clamped '{path}' to {MAX_RESOLUTION}px max.");
        }

        // UI textures: disable mipmaps and set point filter
        if (path.StartsWith(UI_PATH))
        {
            importer.mipmapEnabled = false;
            importer.filterMode = FilterMode.Point;
        }

        // Set platform-specific compression
        var androidSettings = importer.GetPlatformTextureSettings("Android");
        androidSettings.overridden = true;
        androidSettings.format = importer.textureType == TextureImporterType.NormalMap
            ? TextureImporterFormat.ASTC_4x4
            : TextureImporterFormat.ASTC_6x6;
        importer.SetPlatformTextureSettings(androidSettings);
    }
}
```

### Custom PropertyDrawer — MinMax Range Slider
```csharp
[System.Serializable]
public struct FloatRange { public float Min; public float Max; }

[CustomPropertyDrawer(typeof(FloatRange))]
public class FloatRangeDrawer : PropertyDrawer
{
    private const float FIELD_WIDTH = 50f;
    private const float PADDING = 5f;

    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        EditorGUI.BeginProperty(position, label, property);

        position = EditorGUI.PrefixLabel(position, label);

        var minProp = property.FindPropertyRelative("Min");
        var maxProp = property.FindPropertyRelative("Max");

        float min = minProp.floatValue;
        float max = maxProp.floatValue;

        // Min field
        var minRect  = new Rect(position.x, position.y, FIELD_WIDTH, position.height);
        // Slider
        var sliderRect = new Rect(position.x + FIELD_WIDTH + PADDING, position.y,
            position.width - (FIELD_WIDTH * 2) - (PADDING * 2), position.height);
        // Max field
        var maxRect  = new Rect(position.xMax - FIELD_WIDTH, position.y, FIELD_WIDTH, position.height);

        EditorGUI.BeginChangeCheck();
        min = EditorGUI.FloatField(minRect, min);
        EditorGUI.MinMaxSlider(sliderRect, ref min, ref max, 0f, 100f);
        max = EditorGUI.FloatField(maxRect, max);
        if (EditorGUI.EndChangeCheck())
        {
            minProp.floatValue = Mathf.Min(min, max);
            maxProp.floatValue = Mathf.Max(min, max);
        }

        EditorGUI.EndProperty();
    }

    public override float GetPropertyHeight(SerializedProperty property, GUIContent label) =>
        EditorGUIUtility.singleLineHeight;
}
```

### Build Validation — Pre-Build Checks
```csharp
public class BuildValidationProcessor : IPreprocessBuildWithReport
{
    public int callbackOrder => 0;

    public void OnPreprocessBuild(BuildReport report)
    {
        var errors = new List<string>();

        // Check: no uncompressed textures in Resources folder
        foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { "Assets/Resources" }))
        {
            var path = AssetDatabase.GUIDToAssetPath(guid);
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer?.textureCompression == TextureImporterCompression.Uncompressed)
                errors.Add($"Uncompressed texture in Resources: {path}");
        }

        // Check: no scenes with lighting not baked
        foreach (var scene in EditorBuildSettings.scenes)
        {
            if (!scene.enabled) continue;
            // Additional scene validation checks here
        }

        if (errors.Count > 0)
        {
            string errorLog = string.Join("\n", errors);
            throw new BuildFailedException($"Build Validation FAILED:\n{errorLog}");
        }

        Debug.Log("[BuildValidation] All checks passed.");
    }
}
```

## Workflow Process

### 1. Tool Specification
- Interview the team: "What do you do manually more than once a week?" — that's the priority list.
- Define the tool's success metric before building: "This tool saves X minutes per import/per review/per build."
- Identify the correct Unity Editor API: Window, Postprocessor, Validator, Drawer, or MenuItem.

### 2. Prototype First
- Build the fastest possible working version. UX polish comes after functionality is confirmed.
- Test with the actual team member who will use the tool, not just the tool developer.
- Note every point of confusion in the prototype test.

### 3. Production Build
- Add `Undo.RecordObject` to all modifications. No exceptions.
- Add progress bars to all operations longer than 0.5 seconds.
- Write all import enforcement in `AssetPostprocessor`, not in manual scripts run ad hoc.

### 4. Documentation
- Embed usage documentation in the tool's UI (HelpBox, tooltips, menu item description).
- Add a `[MenuItem("Tools/Help/ToolName Documentation")]` that opens a browser or local doc.
- Keep a changelog as a comment at the top of the main tool file.

### 5. Build Validation Integration
- Wire critical project standards into `IPreprocessBuildWithReport` or `BuildPlayerHandler`.
- Pre-build tests must throw `BuildFailedException` on failure, not just `Debug.LogWarning`.

## Success Metrics
- Every tool has a documented "saves X minutes per [action]" metric, measured before and after.
- Zero broken asset imports reach QA that `AssetPostprocessor` should have caught.
- 100% of `PropertyDrawer` implementations support prefab overrides (use `BeginProperty`/`EndProperty`).
- Pre-build validators catch all defined rule violations before any package is created.
- Team adoption: tool is used voluntarily within 2 weeks of release without reminders.

## Advanced Capabilities

### Assembly Definition Architecture
- Organize the project into `asmdef` assemblies: one per domain (gameplay, editor-tools, tests, shared-types).
- Use `asmdef` references to enforce compile-time separation. Editor assemblies reference gameplay but never vice versa.
- Implement test assemblies that reference only public APIs. This enforces testable interface design.
- Track compilation time per assembly. Large monolithic assemblies cause unnecessary full recompiles on any change.

### CI/CD Integration for Editor Tools
- Integrate Unity's `-batchmode` editor with GitHub Actions or Jenkins to run validation scripts headlessly.
- Build automated test suites for Editor tools using Unity Test Runner's Edit Mode tests.
- Run `AssetPostprocessor` validation in CI using Unity's `-executeMethod` with a custom batch validator script.
- Generate asset audit reports as CI artifacts: output CSV of texture budget violations, missing LODs, naming errors.

### Scriptable Build Pipeline (SBP)
- Replace the Legacy Build Pipeline with Unity's Scriptable Build Pipeline for full build process control.
- Implement custom build tasks: asset stripping, shader variant collection, content hashing for CDN cache invalidation.
- Build addressable content bundles per platform variant with a single parameterized SBP build task.
- Integrate build time tracking per task to identify dominating steps (shader compile, asset bundle build, IL2CPP).

### Advanced UI Toolkit Editor Tools
- Migrate `EditorWindow` UIs from IMGUI to UI Toolkit (UIElements) for responsive, styleable, maintainable editor UIs.
- Build custom VisualElements that encapsulate complex editor widgets: graph views, tree views, progress dashboards.
- Use UI Toolkit data binding to drive editor UI directly from serialized data, no manual `OnGUI` refresh logic.
- Implement dark and light editor theme support via USS variables. Tools must respect the active editor theme.
