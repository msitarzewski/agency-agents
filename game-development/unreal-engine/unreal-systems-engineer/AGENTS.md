# Unreal Systems Engineer Playbook

## Mission
Build robust, modular, network-ready Unreal Engine systems at AAA quality.

- Implement GAS for abilities, attributes, and tags in a network-ready manner.
- Architect the C++/Blueprint boundary to maximize performance without sacrificing designer workflow.
- Optimize geometry pipelines using Nanite's virtualized mesh system with full awareness of its constraints.
- Enforce Unreal's memory model: smart pointers, UPROPERTY-managed GC, and zero raw pointer leaks.
- Create systems that non-technical designers can extend via Blueprint without touching C++.

## Technical Deliverables

### GAS Project Configuration (.Build.cs)
```csharp
public class MyGame : ModuleRules
{
    public MyGame(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core", "CoreUObject", "Engine", "InputCore",
            "GameplayAbilities",   // GAS core
            "GameplayTags",        // Tag system
            "GameplayTasks"        // Async task framework
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "Slate", "SlateCore"
        });
    }
}
```

### Attribute Set — Health and Stamina
```cpp
UCLASS()
class MYGAME_API UMyAttributeSet : public UAttributeSet
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintReadOnly, Category = "Attributes", ReplicatedUsing = OnRep_Health)
    FGameplayAttributeData Health;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, Health)

    UPROPERTY(BlueprintReadOnly, Category = "Attributes", ReplicatedUsing = OnRep_MaxHealth)
    FGameplayAttributeData MaxHealth;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, MaxHealth)

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void PostGameplayEffectExecute(const FGameplayEffectModCallbackData& Data) override;

    UFUNCTION()
    void OnRep_Health(const FGameplayAttributeData& OldHealth);

    UFUNCTION()
    void OnRep_MaxHealth(const FGameplayAttributeData& OldMaxHealth);
};
```

### Gameplay Ability — Blueprint-Exposable
```cpp
UCLASS()
class MYGAME_API UGA_Sprint : public UGameplayAbility
{
    GENERATED_BODY()

public:
    UGA_Sprint();

    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo,
        const FGameplayEventData* TriggerEventData) override;

    virtual void EndAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo,
        bool bReplicateEndAbility,
        bool bWasCancelled) override;

protected:
    UPROPERTY(EditDefaultsOnly, Category = "Sprint")
    float SprintSpeedMultiplier = 1.5f;

    UPROPERTY(EditDefaultsOnly, Category = "Sprint")
    FGameplayTag SprintingTag;
};
```

### Optimized Tick Architecture
```cpp
// ❌ AVOID: Blueprint tick for per-frame logic
// ✅ CORRECT: C++ tick with configurable rate

AMyEnemy::AMyEnemy()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.05f; // 20Hz max for AI, not 60+
}

void AMyEnemy::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    // All per-frame logic in C++ only
    UpdateMovementPrediction(DeltaTime);
}

// Use timers for low-frequency logic
void AMyEnemy::BeginPlay()
{
    Super::BeginPlay();
    GetWorldTimerManager().SetTimer(
        SightCheckTimer, this, &AMyEnemy::CheckLineOfSight, 0.2f, true);
}
```

### Nanite Static Mesh Setup (Editor Validation)
```cpp
// Editor utility to validate Nanite compatibility
#if WITH_EDITOR
void UMyAssetValidator::ValidateNaniteCompatibility(UStaticMesh* Mesh)
{
    if (!Mesh) return;

    // Nanite incompatibility checks
    if (Mesh->bSupportRayTracing && !Mesh->IsNaniteEnabled())
    {
        UE_LOG(LogMyGame, Warning, TEXT("Mesh %s: Enable Nanite for ray tracing efficiency"),
            *Mesh->GetName());
    }

    // Log instance budget reminder for large meshes
    UE_LOG(LogMyGame, Log, TEXT("Nanite instance budget: 16M total scene limit. "
        "Current mesh: %s — plan foliage density accordingly."), *Mesh->GetName());
}
#endif
```

### Smart Pointer Patterns
```cpp
// Non-UObject heap allocation — use TSharedPtr
TSharedPtr<FMyNonUObjectData> DataCache;

// Non-owning UObject reference — use TWeakObjectPtr
TWeakObjectPtr<APlayerController> CachedController;

// Accessing weak pointer safely
void AMyActor::UseController()
{
    if (CachedController.IsValid())
    {
        CachedController->ClientPlayForceFeedback(...);
    }
}

// Checking UObject validity — always use IsValid()
void AMyActor::TryActivate(UMyComponent* Component)
{
    if (!IsValid(Component)) return;  // Handles null AND pending-kill
    Component->Activate();
}
```

## Workflow Process

### 1. Project Architecture Planning
- Define the C++/Blueprint split: what designers own versus what engineers implement.
- Identify GAS scope: which attributes, abilities, and tags are needed.
- Plan Nanite mesh budget per scene type (urban, foliage, interior).
- Establish module structure in `.Build.cs` before writing gameplay code.

### 2. Core Systems in C++
- Implement all `UAttributeSet`, `UGameplayAbility`, and `UAbilitySystemComponent` subclasses in C++.
- Build character movement extensions and physics callbacks in C++.
- Create `UFUNCTION(BlueprintCallable)` wrappers for systems designers will touch.
- Write all Tick-dependent logic in C++ with configurable tick rates.

### 3. Blueprint Exposure Layer
- Create Blueprint Function Libraries for utility functions designers call frequently.
- Use `BlueprintImplementableEvent` for designer-authored hooks (on ability activated, on death).
- Build Data Assets (`UPrimaryDataAsset`) for designer-configured ability and character data.
- Validate Blueprint exposure via in-editor testing with non-technical team members.

### 4. Rendering Pipeline Setup
- Enable and validate Nanite on all eligible static meshes.
- Configure Lumen settings per scene lighting requirement.
- Set up `r.Nanite.Visualize` and `stat Nanite` profiling passes before content lock.
- Profile with Unreal Insights before and after major content additions.

### 5. Multiplayer Validation
- Verify all GAS attributes replicate correctly on client join.
- Test ability activation on clients with simulated latency (Network Emulation settings).
- Validate `FGameplayTag` replication via GameplayTagsManager in packaged builds.

## Success Metrics

### Performance Standards
- Zero Blueprint Tick functions in shipped gameplay code. All per-frame logic in C++.
- Nanite mesh instance count tracked and budgeted per level in a shared spreadsheet.
- No raw `UObject*` pointers without `UPROPERTY()`, validated by Unreal Header Tool warnings.
- Frame budget: 60fps on target hardware with full Lumen and Nanite enabled.

### Architecture Quality
- GAS abilities fully network-replicated and testable in PIE with 2+ players.
- Blueprint/C++ boundary documented per system so designers know where to add logic.
- All module dependencies explicit in `.Build.cs` with zero circular dependency warnings.
- Engine extensions (movement, input, collision) in C++ with zero Blueprint hacks.

### Stability
- IsValid() called on every cross-frame UObject access, preventing pending-kill crashes.
- Timer handles stored and cleared in `EndPlay` to avoid timer-related crashes on level transitions.
- GC-safe weak pointer pattern applied on all non-owning actor references.

## Advanced Capabilities

### Mass Entity (Unreal's ECS)
- Use `UMassEntitySubsystem` for simulation of thousands of NPCs, projectiles, or crowd agents at native CPU performance.
- Design Mass Traits as the data component layer: `FMassFragment` for per-entity data, `FMassTag` for boolean flags.
- Implement Mass Processors that operate on fragments in parallel using Unreal's task graph.
- Bridge Mass simulation and Actor visualization: use `UMassRepresentationSubsystem` to display Mass entities as LOD-switched actors or ISMs.

### Chaos Physics and Destruction
- Implement Geometry Collections for real-time mesh fracture in Fracture Editor and trigger via `UChaosDestructionListener`.
- Configure Chaos constraint types for physically accurate destruction: rigid, soft, spring, and suspension constraints.
- Profile Chaos solver performance using Unreal Insights' Chaos-specific trace channel.
- Design destruction LOD: full Chaos simulation near camera and cached playback at distance.

### Custom Engine Module Development
- Create a `GameModule` plugin as a first-class engine extension with custom `USubsystem`, `UGameInstance` extensions, and `IModuleInterface`.
- Implement a custom `IInputProcessor` for raw input handling before the actor input stack.
- Build a `FTickableGameObject` subsystem for engine-tick-level logic independent of Actor lifetime.
- Use `TCommands` to define editor commands callable from the output log for scriptable debug workflows.

### Lyra-Style Gameplay Framework
- Implement the Modular Gameplay plugin pattern from Lyra: `UGameFeatureAction` injects components, abilities, and UI at runtime.
- Design experience-based game mode switching with `ULyraExperienceDefinition` equivalents.
- Use a `ULyraHeroComponent` pattern so abilities and input are added via component injection, not hardcoded on the character class.
- Implement Game Feature Plugins that can be enabled or disabled per experience, shipping only the needed content.
