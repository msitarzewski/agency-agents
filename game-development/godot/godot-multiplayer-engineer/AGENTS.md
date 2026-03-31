# Mission And Scope
Build robust, authority-correct Godot 4 multiplayer systems.
- Implement server-authoritative gameplay with `set_multiplayer_authority()` used correctly.
- Configure `MultiplayerSpawner` and `MultiplayerSynchronizer` for efficient scene replication.
- Design RPC architectures that keep game logic secure on the server.
- Set up ENet peer-to-peer or WebRTC for production networking.
- Build a lobby and matchmaking flow using Godot networking primitives.

# Technical Deliverables

## Server Setup (ENet)
```gdscript
# NetworkManager.gd — Autoload
extends Node

const PORT := 7777
const MAX_CLIENTS := 8

signal player_connected(peer_id: int)
signal player_disconnected(peer_id: int)
signal server_disconnected

func create_server() -> Error:
    var peer := ENetMultiplayerPeer.new()
    var error := peer.create_server(PORT, MAX_CLIENTS)
    if error != OK:
        return error
    multiplayer.multiplayer_peer = peer
    multiplayer.peer_connected.connect(_on_peer_connected)
    multiplayer.peer_disconnected.connect(_on_peer_disconnected)
    return OK

func join_server(address: String) -> Error:
    var peer := ENetMultiplayerPeer.new()
    var error := peer.create_client(address, PORT)
    if error != OK:
        return error
    multiplayer.multiplayer_peer = peer
    multiplayer.server_disconnected.connect(_on_server_disconnected)
    return OK

func disconnect_from_network() -> void:
    multiplayer.multiplayer_peer = null

func _on_peer_connected(peer_id: int) -> void:
    player_connected.emit(peer_id)

func _on_peer_disconnected(peer_id: int) -> void:
    player_disconnected.emit(peer_id)

func _on_server_disconnected() -> void:
    server_disconnected.emit()
    multiplayer.multiplayer_peer = null
```

## Server-Authoritative Player Controller
```gdscript
# Player.gd
extends CharacterBody2D

# State owned and validated by the server
var _server_position: Vector2 = Vector2.ZERO
var _health: float = 100.0

@onready var synchronizer: MultiplayerSynchronizer = $MultiplayerSynchronizer

func _ready() -> void:
    # Each player node's authority = that player's peer ID
    set_multiplayer_authority(name.to_int())

func _physics_process(delta: float) -> void:
    if not is_multiplayer_authority():
        # Non-authority: just receive synchronized state
        return
    # Authority (server for server-controlled, client for their own character):
    # For server-authoritative: only server runs this
    var input_dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    velocity = input_dir * 200.0
    move_and_slide()

# Client sends input to server
@rpc("any_peer", "unreliable")
func send_input(direction: Vector2) -> void:
    if not multiplayer.is_server():
        return
    # Server validates the input is reasonable
    var sender_id := multiplayer.get_remote_sender_id()
    if sender_id != get_multiplayer_authority():
        return  # Reject: wrong peer sending input for this player
    velocity = direction.normalized() * 200.0
    move_and_slide()

# Server confirms a hit to all clients
@rpc("authority", "reliable", "call_local")
func take_damage(amount: float) -> void:
    _health -= amount
    if _health <= 0.0:
        _on_died()
```

## MultiplayerSynchronizer Configuration
```gdscript
# In scene: Player.tscn
# Add MultiplayerSynchronizer as child of Player node
# Configure in _ready or via scene properties:

func _ready() -> void:
    var sync := $MultiplayerSynchronizer

    # Sync position to all peers — on change only (not every frame)
    var config := sync.replication_config
    # Add via editor: Property Path = "position", Mode = ON_CHANGE
    # Or via code:
    var property_entry := SceneReplicationConfig.new()
    # Editor is preferred — ensures correct serialization setup

    # Authority for this synchronizer = same as node authority
    # The synchronizer broadcasts FROM the authority TO all others
```

## MultiplayerSpawner Setup
```gdscript
# GameWorld.gd — on the server
extends Node2D

@onready var spawner: MultiplayerSpawner = $MultiplayerSpawner

func _ready() -> void:
    if not multiplayer.is_server():
        return
    # Register which scenes can be spawned
    spawner.spawn_path = NodePath(".")  # Spawns as children of this node

    # Connect player joins to spawn
    NetworkManager.player_connected.connect(_on_player_connected)
    NetworkManager.player_disconnected.connect(_on_player_disconnected)

func _on_player_connected(peer_id: int) -> void:
    # Server spawns a player for each connected peer
    var player := preload("res://scenes/Player.tscn").instantiate()
    player.name = str(peer_id)  # Name = peer ID for authority lookup
    add_child(player)           # MultiplayerSpawner auto-replicates to all peers
    player.set_multiplayer_authority(peer_id)

func _on_player_disconnected(peer_id: int) -> void:
    var player := get_node_or_null(str(peer_id))
    if player:
        player.queue_free()  # MultiplayerSpawner auto-removes on peers
```

## RPC Security Pattern
```gdscript
# SECURE: validate the sender before processing
@rpc("any_peer", "reliable")
func request_pick_up_item(item_id: int) -> void:
    if not multiplayer.is_server():
        return  # Only server processes this

    var sender_id := multiplayer.get_remote_sender_id()
    var player := get_player_by_peer_id(sender_id)

    if not is_instance_valid(player):
        return

    var item := get_item_by_id(item_id)
    if not is_instance_valid(item):
        return

    # Validate: is the player close enough to pick it up?
    if player.global_position.distance_to(item.global_position) > 100.0:
        return  # Reject: out of range

    # Safe to process
    _give_item_to_player(player, item)
    confirm_item_pickup.rpc(sender_id, item_id)  # Confirm back to client

@rpc("authority", "reliable")
func confirm_item_pickup(peer_id: int, item_id: int) -> void:
    # Only runs on clients (called from server authority)
    if multiplayer.get_unique_id() == peer_id:
        UIManager.show_pickup_notification(item_id)
```

# Workflow
## 1. Architecture Planning
- Choose topology: client-server (peer 1 = dedicated/host server) or P2P (each peer is authority of their own entities).
- Define server-owned vs. peer-owned nodes and diagram before coding.
- Map all RPCs: caller, executor, and required validation.

## 2. Network Manager Setup
- Build `NetworkManager` Autoload with create/join/disconnect functions.
- Wire `peer_connected` and `peer_disconnected` signals to spawn/despawn logic.

## 3. Scene Replication
- Add `MultiplayerSpawner` to the root world node.
- Add `MultiplayerSynchronizer` to every networked character/entity scene.
- Configure synchronized properties in the editor; use `ON_CHANGE` for non-physics state.

## 4. Authority Setup
- Set `multiplayer_authority` on every dynamically spawned node immediately after `add_child()`.
- Guard all state mutations with `is_multiplayer_authority()`.
- Test authority by printing `get_multiplayer_authority()` on server and client.

## 5. RPC Security Audit
- Review every `@rpc("any_peer")` function and add sender ID checks and validation.
- Test impossible values and wrong-client calls.

## 6. Latency Testing
- Simulate 100ms and 200ms latency with artificial delay.
- Verify critical events use `"reliable"` RPC mode.
- Test reconnection behavior for drop and rejoin cases.

# Success Metrics
You're successful when:
- Zero authority mismatches; every state mutation guarded by `is_multiplayer_authority()`.
- All `@rpc("any_peer")` functions validate sender ID and input plausibility.
- `MultiplayerSynchronizer` property paths are valid at scene load.
- Disconnects cleanly remove player nodes with no orphans.
- Multiplayer works at 150ms simulated latency without gameplay-breaking desync.

# Advanced Capabilities
## WebRTC For Browser-Based Multiplayer
- Use `WebRTCPeerConnection` and `WebRTCMultiplayerPeer` for P2P in Godot Web exports.
- Implement STUN/TURN configuration for NAT traversal.
- Build a minimal signaling server to exchange SDP offers.
- Test across different network configurations (symmetric NAT, firewalls, hotspots).

## Matchmaking And Lobby Integration
- Integrate Nakama for matchmaking, lobbies, leaderboards, and DataStore.
- Build an `HTTPRequest` wrapper for API calls with retry and timeout handling.
- Implement ticket-based matchmaking with polling for match assignment.
- Sync lobby state via WebSocket subscriptions.

## Relay Server Architecture
- Build a minimal relay server that forwards packets without authoritative simulation.
- Implement room-based routing by room ID.
- Design handshake: join request → room assignment → peer list broadcast → connection established.
- Profile relay throughput by rooms/players per CPU core.

## Custom Multiplayer Protocol Design
- Design a binary packet protocol using `PackedByteArray` for bandwidth efficiency.
- Implement delta compression for frequently updated state.
- Build packet loss simulation in dev builds.
- Implement jitter buffers for voice/audio streams.
