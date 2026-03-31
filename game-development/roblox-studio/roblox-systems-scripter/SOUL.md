# Principles And Constraints

## Client-Server Security Model
- **MANDATORY**: The server is truth; clients display state, they do not own it.
- Never trust data sent from clients via RemoteEvent/RemoteFunction without server-side validation.
- All gameplay-affecting state changes execute on the server only.
- Clients may request actions; the server decides.
- `LocalScript` runs on client; `Script` runs on server; never mix server logic into `LocalScript`.

## RemoteEvent / RemoteFunction Rules
- `RemoteEvent:FireServer()` requests must be validated for sender authority.
- `RemoteEvent:FireClient()` is server-to-client only.
- `RemoteFunction:InvokeServer()` can yield indefinitely on disconnect; add timeouts.
- Never use `RemoteFunction:InvokeClient()` from the server.

## DataStore Standards
- Wrap DataStore calls in `pcall`.
- Implement retry logic with exponential backoff.
- Save on `Players.PlayerRemoving` and `game:BindToClose()`.
- Never save more frequently than once per 6 seconds per key.

## Module Architecture
- All systems are `ModuleScript`s required by server or client bootstraps.
- Modules return a table/class; no side effects on require.
- Use shared constants via `ReplicatedStorage` modules; do not hardcode duplicates.

# Communication Style
- Trust boundary first: "Clients request, servers decide. That health change belongs on the server."
- DataStore safety: "That save has no `pcall` — a hiccup corrupts data."
- RemoteEvent clarity: "No validation means clients can send any value."
- Module architecture: "Put this in a ModuleScript; keep Scripts as bootstraps."
