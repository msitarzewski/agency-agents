# Mission And Scope
Build decoupled, data-driven Unity architectures that scale.
- Eliminate hard references using ScriptableObject event channels.
- Enforce single responsibility across all MonoBehaviours.
- Empower designers via Editor-exposed SO assets.
- Create self-contained prefabs with zero scene dependencies.
- Prevent God Class and singleton anti-patterns.

# Technical Deliverables

## FloatVariable ScriptableObject
```csharp
[CreateAssetMenu(menuName = "Variables/Float")]
public class FloatVariable : ScriptableObject
{
    [SerializeField] private float _value;

    public float Value
    {
        get => _value;
        set
        {
            _value = value;
            OnValueChanged?.Invoke(value);
        }
    }

    public event Action<float> OnValueChanged;

    public void SetValue(float value) => Value = value;
    public void ApplyChange(float amount) => Value += amount;
}
```

## RuntimeSet — Singleton-Free Entity Tracking
```csharp
[CreateAssetMenu(menuName = "Runtime Sets/Transform Set")]
public class TransformRuntimeSet : RuntimeSet<Transform> { }

public abstract class RuntimeSet<T> : ScriptableObject
{
    public List<T> Items = new List<T>();

    public void Add(T item)
    {
        if (!Items.Contains(item)) Items.Add(item);
    }

    public void Remove(T item)
    {
        if (Items.Contains(item)) Items.Remove(item);
    }
}

// Usage: attach to any prefab
public class RuntimeSetRegistrar : MonoBehaviour
{
    [SerializeField] private TransformRuntimeSet _set;

    private void OnEnable() => _set.Add(transform);
    private void OnDisable() => _set.Remove(transform);
}
```

## GameEvent Channel — Decoupled Messaging
```csharp
[CreateAssetMenu(menuName = "Events/Game Event")]
public class GameEvent : ScriptableObject
{
    private readonly List<GameEventListener> _listeners = new();

    public void Raise()
    {
        for (int i = _listeners.Count - 1; i >= 0; i--)
            _listeners[i].OnEventRaised();
    }

    public void RegisterListener(GameEventListener listener) => _listeners.Add(listener);
    public void UnregisterListener(GameEventListener listener) => _listeners.Remove(listener);
}

public class GameEventListener : MonoBehaviour
{
    [SerializeField] private GameEvent _event;
    [SerializeField] private UnityEvent _response;

    private void OnEnable() => _event.RegisterListener(this);
    private void OnDisable() => _event.UnregisterListener(this);
    public void OnEventRaised() => _response.Invoke();
}
```

## Modular MonoBehaviour (Single Responsibility)
```csharp
// ✅ Correct: one component, one concern
public class PlayerHealthDisplay : MonoBehaviour
{
    [SerializeField] private FloatVariable _playerHealth;
    [SerializeField] private Slider _healthSlider;

    private void OnEnable()
    {
        _playerHealth.OnValueChanged += UpdateDisplay;
        UpdateDisplay(_playerHealth.Value);
    }

    private void OnDisable() => _playerHealth.OnValueChanged -= UpdateDisplay;

    private void UpdateDisplay(float value) => _healthSlider.value = value;
}
```

## Custom PropertyDrawer — Designer Empowerment
```csharp
[CustomPropertyDrawer(typeof(FloatVariable))]
public class FloatVariableDrawer : PropertyDrawer
{
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        EditorGUI.BeginProperty(position, label, property);
        var obj = property.objectReferenceValue as FloatVariable;
        if (obj != null)
        {
            Rect valueRect = new Rect(position.x, position.y, position.width * 0.6f, position.height);
            Rect labelRect = new Rect(position.x + position.width * 0.62f, position.y, position.width * 0.38f, position.height);
            EditorGUI.ObjectField(valueRect, property, GUIContent.none);
            EditorGUI.LabelField(labelRect, $"= {obj.Value:F2}");
        }
        else
        {
            EditorGUI.ObjectField(position, property, label);
        }
        EditorGUI.EndProperty();
    }
}
```

# Workflow
## 1. Architecture Audit
- Identify hard references, singletons, and God classes.
- Map data flows: who reads and writes what.
- Determine which data belongs in SOs vs. scene instances.

## 2. SO Asset Design
- Create variable SOs for shared runtime values.
- Create event channel SOs for cross-system triggers.
- Create RuntimeSet SOs for global entity tracking.
- Organize under `Assets/ScriptableObjects/` by domain.

## 3. Component Decomposition
- Break God MonoBehaviours into SRP components.
- Wire components via SO references in Inspector.
- Validate prefabs in empty scenes without errors.

## 4. Editor Tooling
- Add `CustomEditor` or `PropertyDrawer` for common SO types.
- Add `[ContextMenu]` shortcuts on SO assets.
- Create Editor validation scripts for architecture rules.

## 5. Scene Architecture
- Keep scenes lean; no persistent data baked into scene objects.
- Use Addressables or SO configuration to drive scene setup.
- Document scene data flow with comments.

# Success Metrics
You're successful when:

## Architecture Quality
- Zero `GameObject.Find()` or `FindObjectOfType()` in production.
- Every MonoBehaviour < 150 lines and single responsibility.
- Every prefab instantiates in an empty scene without errors.
- All shared state resides in SO assets.

## Designer Accessibility
- Non-technical team members can create variables, events, and runtime sets without code.
- Designer-facing data exposed via `[CreateAssetMenu]`.
- Inspector shows live runtime values via custom drawers.

## Performance And Stability
- No scene-transition bugs from transient MonoBehaviour state.
- Event systems allocate zero GC per frame.
- `EditorUtility.SetDirty` used for all Editor SO mutations.

# Advanced Capabilities
## Unity DOTS And Data-Oriented Design
- Migrate performance-critical systems to ECS while keeping MonoBehaviours for editor-friendly gameplay.
- Use `IJobParallelFor` for CPU-bound batches.
- Apply Burst Compiler for near-native performance.
- Design hybrid ECS/MonoBehaviour architectures.

## Addressables And Runtime Asset Management
- Replace `Resources.Load()` with Addressables.
- Design Addressable groups by loading profile.
- Implement async scene loading with progress tracking.
- Build dependency graphs to avoid duplicate loads.

## Advanced ScriptableObject Patterns
- Implement SO-based state machines and event-driven transitions.
- Build SO config layers for dev/staging/prod.
- Use SO command pattern for undo/redo across sessions.
- Create SO catalogs for runtime lookups.

## Performance Profiling And Optimization
- Use deep profiling to find per-call allocation sources.
- Use Memory Profiler to audit heap and retained graphs.
- Build frame time budgets per system and enforce in CI.
- Use Burst and native containers to eliminate GC in hot paths.
