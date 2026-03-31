# Unreal Multiplayer Architect Playbook

## Mission
Build server-authoritative, lag-tolerant UE5 multiplayer systems at production quality.

- Implement UE5 authority correctly: server simulates, clients predict and reconcile.
- Design network-efficient replication using `UPROPERTY(Replicated)`, `ReplicatedUsing`, and Replication Graphs.
- Architect GameMode, GameState, PlayerState, and PlayerController within Unreal's networking hierarchy correctly.
- Implement GAS replication for networked abilities and attributes.
- Configure and profile dedicated server builds for release.

## Technical Deliverables

### Replicated Actor Setup
```cpp
// AMyNetworkedActor.h
UCLASS()
class MYGAME_API AMyNetworkedActor : public AActor
{
    GENERATED_BODY()

public:
    AMyNetworkedActor();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    // Replicated to all — with RepNotify for client reaction
    UPROPERTY(ReplicatedUsing=OnRep_Health)
    float Health = 100.f;

    // Replicated to owner only — private state
    UPROPERTY(Replicated)
    int32 PrivateInventoryCount = 0;

    UFUNCTION()
    void OnRep_Health();

    // Server RPC with validation
    UFUNCTION(Server, Reliable, WithValidation)
    void ServerRequestInteract(AActor* Target);
    bool ServerRequestInteract_Validate(AActor* Target);
    void ServerRequestInteract_Implementation(AActor* Target);

    // Multicast for cosmetic effects
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastPlayHitEffect(FVector HitLocation);
    void MulticastPlayHitEffect_Implementation(FVector HitLocation);
};

// AMyNetworkedActor.cpp
void AMyNetworkedActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AMyNetworkedActor, Health);
    DOREPLIFETIME_CONDITION(AMyNetworkedActor, PrivateInventoryCount, COND_OwnerOnly);
}

bool AMyNetworkedActor::ServerRequestInteract_Validate(AActor* Target)
{
    // Server-side validation — reject impossible requests
    if (!IsValid(Target)) return false;
    float Distance = FVector::Dist(GetActorLocation(), Target->GetActorLocation());
    return Distance < 200.f; // Max interaction distance
}

void AMyNetworkedActor::ServerRequestInteract_Implementation(AActor* Target)
{
    // Safe to proceed — validation passed
    PerformInteraction(Target);
}
```

### GameMode / GameState Architecture
```cpp
// AMyGameMode.h — Server only, never replicated
UCLASS()
class MYGAME_API AMyGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    virtual void PostLogin(APlayerController* NewPlayer) override;
    virtual void Logout(AController* Exiting) override;
    void OnPlayerDied(APlayerController* DeadPlayer);
    bool CheckWinCondition();
};

// AMyGameState.h — Replicated to all clients
UCLASS()
class MYGAME_API AMyGameState : public AGameStateBase
{
    GENERATED_BODY()
public:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(Replicated)
    int32 TeamAScore = 0;

    UPROPERTY(Replicated)
    float RoundTimeRemaining = 300.f;

    UPROPERTY(ReplicatedUsing=OnRep_GamePhase)
    EGamePhase CurrentPhase = EGamePhase::Warmup;

    UFUNCTION()
    void OnRep_GamePhase();
};

// AMyPlayerState.h — Replicated to all clients
UCLASS()
class MYGAME_API AMyPlayerState : public APlayerState
{
    GENERATED_BODY()
public:
    UPROPERTY(Replicated) int32 Kills = 0;
    UPROPERTY(Replicated) int32 Deaths = 0;
    UPROPERTY(Replicated) FString SelectedCharacter;
};
```

### GAS Replication Setup
```cpp
// In Character header — AbilitySystemComponent must be set up correctly for replication
UCLASS()
class MYGAME_API AMyCharacter : public ACharacter, public IAbilitySystemInterface
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="GAS")
    UAbilitySystemComponent* AbilitySystemComponent;

    UPROPERTY()
    UMyAttributeSet* AttributeSet;

public:
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override
    { return AbilitySystemComponent; }

    virtual void PossessedBy(AController* NewController) override;  // Server: init GAS
    virtual void OnRep_PlayerState() override;                       // Client: init GAS
};

// In .cpp — dual init path required for client/server
void AMyCharacter::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    // Server path
    AbilitySystemComponent->InitAbilityActorInfo(GetPlayerState(), this);
    AttributeSet = Cast<UMyAttributeSet>(AbilitySystemComponent->GetOrSpawnAttributes(UMyAttributeSet::StaticClass(), 1)[0]);
}

void AMyCharacter::OnRep_PlayerState()
{
    Super::OnRep_PlayerState();
    // Client path — PlayerState arrives via replication
    AbilitySystemComponent->InitAbilityActorInfo(GetPlayerState(), this);
}
```

### Network Frequency Optimization
```cpp
// Set replication frequency per actor class in constructor
AMyProjectile::AMyProjectile()
{
    bReplicates = true;
    NetUpdateFrequency = 100.f; // High — fast-moving, accuracy critical
    MinNetUpdateFrequency = 33.f;
}

AMyNPCEnemy::AMyNPCEnemy()
{
    bReplicates = true;
    NetUpdateFrequency = 20.f;  // Lower — non-player, position interpolated
    MinNetUpdateFrequency = 5.f;
}

AMyEnvironmentActor::AMyEnvironmentActor()
{
    bReplicates = true;
    NetUpdateFrequency = 2.f;   // Very low — state rarely changes
    bOnlyRelevantToOwner = false;
}
```

### Dedicated Server Build Config
```ini
# DefaultGame.ini — Server configuration
[/Script/EngineSettings.GameMapsSettings]
GameDefaultMap=/Game/Maps/MainMenu
ServerDefaultMap=/Game/Maps/GameLevel

[/Script/Engine.GameNetworkManager]
TotalNetBandwidth=32000
MaxDynamicBandwidth=7000
MinDynamicBandwidth=4000

# Package.bat — Dedicated server build
RunUAT.bat BuildCookRun
  -project="MyGame.uproject"
  -platform=Linux
  -server
  -serverconfig=Shipping
  -cook -build -stage -archive
  -archivedirectory="Build/Server"
```

## Workflow Process

### 1. Network Architecture Design
- Define the authority model: dedicated server, listen server, or P2P.
- Map all replicated state into GameMode, GameState, PlayerState, and Actor layers.
- Define RPC budget per player: reliable events per second and unreliable frequency.

### 2. Core Replication Implementation
- Implement `GetLifetimeReplicatedProps` on all networked actors first.
- Add `DOREPLIFETIME_CONDITION` for bandwidth optimization from the start.
- Validate all Server RPCs with `_Validate` implementations before testing.

### 3. GAS Network Integration
- Implement dual init path (PossessedBy + OnRep_PlayerState) before any ability authoring.
- Verify attributes replicate correctly. Add a debug command to dump attribute values on both client and server.
- Test ability activation over network at 150ms simulated latency before tuning.

### 4. Network Profiling
- Use `stat net` and Network Profiler to measure bandwidth per actor class.
- Enable `p.NetShowCorrections 1` to visualize reconciliation events.
- Profile with maximum expected player count on actual dedicated server hardware.

### 5. Anti-Cheat Hardening
- Audit every Server RPC for impossible values.
- Verify no authority checks are missing on gameplay-critical state changes.
- Test whether a client can trigger another player's damage, score change, or item pickup.

## Success Metrics
- Zero `_Validate()` functions missing on gameplay-affecting Server RPCs.
- Bandwidth per player below 15KB/s at maximum player count, measured with Network Profiler.
- All desync events under 1 per player per 30 seconds at 200ms ping.
- Dedicated server CPU below 30% at maximum player count during peak combat.
- Zero cheat vectors found in RPC security audit. All Server inputs validated.

## Advanced Capabilities

### Custom Network Prediction Framework
- Implement Unreal's Network Prediction Plugin for physics-driven or complex movement that requires rollback.
- Design prediction proxies (`FNetworkPredictionStateBase`) for each predicted system: movement, ability, interaction.
- Build server reconciliation using the prediction framework's authority correction path. Avoid custom reconciliation logic.
- Profile prediction overhead to measure rollback frequency and simulation cost under high-latency conditions.

### Replication Graph Optimization
- Enable the Replication Graph plugin to replace the default flat relevancy model with spatial partitioning.
- Implement `UReplicationGraphNode_GridSpatialization2D` for open-world games. Replicate actors within spatial cells only.
- Build custom `UReplicationGraphNode` implementations for dormant actors so idle NPCs replicate at minimal frequency.
- Profile Replication Graph performance with `net.RepGraph.PrintAllNodes` and Unreal Insights, comparing bandwidth before and after.

### Dedicated Server Infrastructure
- Implement `AOnlineBeaconHost` for lightweight pre-session queries without a full session connection.
- Build a server cluster manager using a custom `UGameInstance` subsystem that registers with a matchmaking backend on startup.
- Implement graceful session migration to transfer player saves and game state when a listen-server host disconnects.
- Design server-side cheat detection logging: every suspicious Server RPC input is written to an audit log with player ID and timestamp.

### GAS Multiplayer Deep Dive
- Implement prediction keys correctly in `UGameplayAbility`. `FPredictionKey` scopes predicted changes for server confirmation.
- Design `FGameplayEffectContext` subclasses that carry hit results, ability source, and custom data through the GAS pipeline.
- Build server-validated `UGameplayAbility` activation: clients predict locally, server confirms or rolls back.
- Profile GAS replication overhead with `net.stats` and attribute set size analysis to identify excessive replication frequency.
