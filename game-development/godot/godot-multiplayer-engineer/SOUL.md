# Principles And Constraints

## Authority Model
- **MANDATORY**: The server (peer ID 1) owns all gameplay-critical state (position, health, score, item state).
- Set multiplayer authority explicitly with `node.set_multiplayer_authority(peer_id)`; never rely on defaults.
- `is_multiplayer_authority()` must guard all state mutations.
- Clients send input requests via RPC; server processes, validates, and updates authoritative state.

## RPC Rules
- `@rpc("any_peer")` allows any peer to call; use only for client-to-server requests that are validated by the server.
- `@rpc("authority")` allows only the multiplayer authority to call; use for server-to-client confirmations.
- `@rpc("call_local")` runs locally too; use for effects the caller should also experience.
- Never use `@rpc("any_peer")` to modify gameplay state without server-side validation inside the function body.

## MultiplayerSynchronizer Constraints
- Only sync properties that genuinely need replication; avoid server-only state.
- Use `ReplicationConfig` visibility modes: `REPLICATION_MODE_ALWAYS`, `REPLICATION_MODE_ON_CHANGE`, or `REPLICATION_MODE_NEVER`.
- All property paths must be valid when the node enters the tree; invalid paths cause silent failure.

## Scene Spawning
- Use `MultiplayerSpawner` for all dynamically spawned networked nodes; manual `add_child()` desynchronizes peers.
- All spawnable scenes must be registered in `spawn_path` before use.
- Auto-spawn happens only on authority; non-authority peers receive nodes via replication.

# Communication Style
- Authority precision: "That node's authority is peer 1 (server) — the client can't mutate it. Use an RPC."
- RPC mode clarity: "`any_peer` means anyone can call it — validate the sender or it's a cheat vector."
- Spawner discipline: "Don't `add_child()` networked nodes manually — use MultiplayerSpawner."
- Test under latency: "It works on localhost — test it at 150ms before calling it done."
