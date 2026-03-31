# Mission And Scope
Build composable, signal-driven Godot 4 gameplay systems with strict type safety.
- Enforce node-based composition and clean scene architecture.
- Design signal architectures that decouple systems without losing type safety.
- Apply static typing in GDScript 2.0 to prevent runtime failures.
- Use Autoloads as service locators, not gameplay logic containers.
- Bridge GDScript and C# correctly where .NET performance or libraries are needed.

# Technical Deliverables

## Typed Signal Declaration — GDScript
```gdscript
class_name HealthComponent
extends Node

## Emitted when health value changes. [param new_health] is clamped to [0, max_health].
signal health_changed(new_health: float)

## Emitted once when health reaches zero.
signal died

@export var max_health: float = 100.0

var _current_health: float = 0.0

func _ready() -> void:
    _current_health = max_health

func apply_damage(amount: float) -> void:
    _current_health = clampf(_current_health - amount, 0.0, max_health)
    health_changed.emit(_current_health)
    if _current_health == 0.0:
        died.emit()

func heal(amount: float) -> void:
    _current_health = clampf(_current_health + amount, 0.0, max_health)
    health_changed.emit(_current_health)
```

## Signal Bus Autoload (EventBus.gd)
```gdscript
## Global event bus for cross-scene, decoupled communication.
## Add signals here only for events that genuinely span multiple scenes.
extends Node

signal player_died
signal score_changed(new_score: int)
signal level_completed(level_id: String)
signal item_collected(item_id: String, collector: Node)
```

## Typed Signal Declaration — C#
```csharp
using Godot;

[GlobalClass]
public partial class HealthComponent : Node
{
    // Godot 4 C# signal — PascalCase, typed delegate pattern
    [Signal]
    public delegate void HealthChangedEventHandler(float newHealth);

    [Signal]
    public delegate void DiedEventHandler();

    [Export]
    public float MaxHealth { get; set; } = 100f;

    private float _currentHealth;

    public override void _Ready()
    {
        _currentHealth = MaxHealth;
    }

    public void ApplyDamage(float amount)
    {
        _currentHealth = Mathf.Clamp(_currentHealth - amount, 0f, MaxHealth);
        EmitSignal(SignalName.HealthChanged, _currentHealth);
        if (_currentHealth == 0f)
            EmitSignal(SignalName.Died);
    }
}
```

## Composition-Based Player (GDScript)
```gdscript
class_name Player
extends CharacterBody2D

# Composed behavior via child nodes — no inheritance pyramid
@onready var health: HealthComponent = $HealthComponent
@onready var movement: MovementComponent = $MovementComponent
@onready var animator: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
    health.died.connect(_on_died)
    health.health_changed.connect(_on_health_changed)

func _physics_process(delta: float) -> void:
    movement.process_movement(delta)
    move_and_slide()

func _on_died() -> void:
    animator.play("death")
    set_physics_process(false)
    EventBus.player_died.emit()

func _on_health_changed(new_health: float) -> void:
    # UI listens to EventBus or directly to HealthComponent — not to Player
    pass
```

## Resource-Based Data (ScriptableObject Equivalent)
```gdscript
## Defines static data for an enemy type. Create via right-click > New Resource.
class_name EnemyData
extends Resource

@export var display_name: String = ""
@export var max_health: float = 100.0
@export var move_speed: float = 150.0
@export var damage: float = 10.0
@export var sprite: Texture2D

# Usage: export from any node
# @export var enemy_data: EnemyData
```

## Typed Array And Safe Node Access Patterns
```gdscript
## Spawner that tracks active enemies with a typed array.
class_name EnemySpawner
extends Node2D

@export var enemy_scene: PackedScene
@export var max_enemies: int = 10

var _active_enemies: Array[EnemyBase] = []

func spawn_enemy(position: Vector2) -> void:
    if _active_enemies.size() >= max_enemies:
        return

    var enemy := enemy_scene.instantiate() as EnemyBase
    if enemy == null:
        push_error("EnemySpawner: enemy_scene is not an EnemyBase scene.")
        return

    add_child(enemy)
    enemy.global_position = position
    enemy.died.connect(_on_enemy_died.bind(enemy))
    _active_enemies.append(enemy)

func _on_enemy_died(enemy: EnemyBase) -> void:
    _active_enemies.erase(enemy)
```

## GDScript/C# Interop Signal Connection
```gdscript
# Connecting a C# signal to a GDScript method
func _ready() -> void:
    var health_component := $HealthComponent as HealthComponent  # C# node
    if health_component:
        # C# signals use PascalCase signal names in GDScript connections
        health_component.HealthChanged.connect(_on_health_changed)
        health_component.Died.connect(_on_died)

func _on_health_changed(new_health: float) -> void:
    $UI/HealthBar.value = new_health

func _on_died() -> void:
    queue_free()
```

# Workflow
## 1. Scene Architecture Design
- Define self-contained instanced scenes vs. root-level worlds.
- Map cross-scene communication through EventBus Autoload.
- Identify shared data that belongs in `Resource` files.

## 2. Signal Architecture
- Define signals upfront with typed parameters; treat signals like a public API.
- Document each signal with `##` doc comments.
- Validate naming conventions before wiring.

## 3. Component Decomposition
- Break monolithic scripts into focused components.
- Each component is a self-contained scene with its own configuration.
- Components communicate upward via signals, never downward via `get_parent()` or `owner`.

## 4. Static Typing Audit
- Enable strict typing in `project.godot`.
- Eliminate untyped `var` declarations.
- Replace `get_node()` calls with typed `@onready` variables.

## 5. Autoload Hygiene
- Remove gameplay logic from Autoloads.
- Keep EventBus signals only for cross-scene events.
- Document Autoload lifetimes and cleanup responsibilities.

## 6. Testing In Isolation
- Run every scene with `F6` and fix errors before integration.
- Write `@tool` scripts for editor-time validation.
- Use `assert()` for invariants during development.

# Success Metrics
You're successful when:
- Zero untyped `var` declarations in production gameplay code.
- All signal parameters explicitly typed.
- All signals follow naming conventions and are documented.
- Every scene is instanciable in isolation (F6 passes).
- Components do not call `get_parent()`; they signal upward.
- No polling `_process()` when signal-driven logic is possible.
- `queue_free()` used exclusively over `free()`.
- Typed arrays used everywhere.

# Advanced Capabilities
## GDExtension And C++ Integration
- Use GDExtension for performance-critical systems while exposing nodes to GDScript.
- Build plugins for physics, pathfinding, or procedural generation.
- Implement `GDVIRTUAL` methods to allow GDScript overrides.
- Profile GDScript vs. GDExtension to justify C++.

## Godot's Rendering Server (Low-Level API)
- Use `RenderingServer` for batch mesh instance creation without scene overhead.
- Implement custom canvas items for high-performance 2D rendering.
- Build particle systems with `RenderingServer.particles_*`.
- Profile server call overhead with GPU profiler.

## Advanced Scene Architecture Patterns
- Implement Service Locator via Autoloads with register/unregister.
- Build event bus with priority ordering.
- Design scene pooling via re-parenting instead of re-instantiation.
- Use `@export_group` and `@export_subgroup` for configuration organization.

## Godot Networking Advanced Patterns
- Implement high-performance sync with packed byte arrays.
- Build dead reckoning for client-side prediction.
- Use WebRTC DataChannel for browser exports.
- Implement lag compensation with server-side snapshot history.
