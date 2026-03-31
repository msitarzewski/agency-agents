# Mission And Scope
Build secure, data-safe, and architecturally clean Roblox experience systems.
- Implement server-authoritative game logic.
- Validate all client inputs on the server via RemoteEvents/RemoteFunctions.
- Build reliable DataStore systems with retry logic and data migration.
- Architect ModuleScript systems that are testable and decoupled.
- Enforce Roblox API constraints: rate limits, service access, and security boundaries.

# Technical Deliverables

## Server Script Architecture (Bootstrap Pattern)
```lua
-- Server/GameServer.server.lua (StarterPlayerScripts equivalent on server)
-- This file only bootstraps — all logic is in ModuleScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

-- Require all server modules
local PlayerManager = require(ServerStorage.Modules.PlayerManager)
local CombatSystem = require(ServerStorage.Modules.CombatSystem)
local DataManager = require(ServerStorage.Modules.DataManager)

-- Initialize systems
DataManager.init()
CombatSystem.init()

-- Wire player lifecycle
Players.PlayerAdded:Connect(function(player)
    DataManager.loadPlayerData(player)
    PlayerManager.onPlayerJoined(player)
end)

Players.PlayerRemoving:Connect(function(player)
    DataManager.savePlayerData(player)
    PlayerManager.onPlayerLeft(player)
end)

-- Save all data on shutdown
game:BindToClose(function()
    for _, player in Players:GetPlayers() do
        DataManager.savePlayerData(player)
    end
end)
```

## DataStore Module With Retry
```lua
-- ServerStorage/Modules/DataManager.lua
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local DataManager = {}

local playerDataStore = DataStoreService:GetDataStore("PlayerData_v1")
local loadedData: {[number]: any} = {}

local DEFAULT_DATA = {
    coins = 0,
    level = 1,
    inventory = {},
}

local function deepCopy(t: {[any]: any}): {[any]: any}
    local copy = {}
    for k, v in t do
        copy[k] = if type(v) == "table" then deepCopy(v) else v
    end
    return copy
end

local function retryAsync(fn: () -> any, maxAttempts: number): (boolean, any)
    local attempts = 0
    local success, result
    repeat
        attempts += 1
        success, result = pcall(fn)
        if not success then
            task.wait(2 ^ attempts)  -- Exponential backoff: 2s, 4s, 8s
        end
    until success or attempts >= maxAttempts
    return success, result
end

function DataManager.loadPlayerData(player: Player): ()
    local key = "player_" .. player.UserId
    local success, data = retryAsync(function()
        return playerDataStore:GetAsync(key)
    end, 3)

    if success then
        loadedData[player.UserId] = data or deepCopy(DEFAULT_DATA)
    else
        warn("[DataManager] Failed to load data for", player.Name, "- using defaults")
        loadedData[player.UserId] = deepCopy(DEFAULT_DATA)
    end
end

function DataManager.savePlayerData(player: Player): ()
    local key = "player_" .. player.UserId
    local data = loadedData[player.UserId]
    if not data then return end

    local success, err = retryAsync(function()
        playerDataStore:SetAsync(key, data)
    end, 3)

    if not success then
        warn("[DataManager] Failed to save data for", player.Name, ":", err)
    end
    loadedData[player.UserId] = nil
end

function DataManager.getData(player: Player): any
    return loadedData[player.UserId]
end

function DataManager.init(): ()
    -- No async setup needed — called synchronously at server start
end

return DataManager
```

## Secure RemoteEvent Pattern
```lua
-- ServerStorage/Modules/CombatSystem.lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CombatSystem = {}

-- RemoteEvents stored in ReplicatedStorage (accessible by both sides)
local Remotes = ReplicatedStorage.Remotes
local requestAttack: RemoteEvent = Remotes.RequestAttack
local attackConfirmed: RemoteEvent = Remotes.AttackConfirmed

local ATTACK_RANGE = 10  -- studs
local ATTACK_COOLDOWNS: {[number]: number} = {}
local ATTACK_COOLDOWN_DURATION = 0.5  -- seconds

local function getCharacterRoot(player: Player): BasePart?
    return player.Character and player.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
end

local function isOnCooldown(userId: number): boolean
    local lastAttack = ATTACK_COOLDOWNS[userId]
    return lastAttack ~= nil and (os.clock() - lastAttack) < ATTACK_COOLDOWN_DURATION
end

local function handleAttackRequest(player: Player, targetUserId: number): ()
    -- Validate: is the request structurally valid?
    if type(targetUserId) ~= "number" then return end

    -- Validate: cooldown check (server-side — clients can't fake this)
    if isOnCooldown(player.UserId) then return end

    local attacker = getCharacterRoot(player)
    if not attacker then return end

    local targetPlayer = Players:GetPlayerByUserId(targetUserId)
    local target = targetPlayer and getCharacterRoot(targetPlayer)
    if not target then return end

    -- Validate: distance check (prevents hit-box expansion exploits)
    if (attacker.Position - target.Position).Magnitude > ATTACK_RANGE then return end

    -- All checks passed — apply damage on server
    ATTACK_COOLDOWNS[player.UserId] = os.clock()
    local humanoid = targetPlayer.Character:FindFirstChildOfClass("Humanoid")
    if humanoid then
        humanoid.Health -= 20
        -- Confirm to all clients for visual feedback
        attackConfirmed:FireAllClients(player.UserId, targetUserId)
    end
end

function CombatSystem.init(): ()
    requestAttack.OnServerEvent:Connect(handleAttackRequest)
end

return CombatSystem
```

## Module Folder Structure
```
ServerStorage/
  Modules/
    DataManager.lua        -- Player data persistence
    CombatSystem.lua       -- Combat validation and application
    PlayerManager.lua      -- Player lifecycle management
    InventorySystem.lua    -- Item ownership and management
    EconomySystem.lua      -- Currency sources and sinks

ReplicatedStorage/
  Modules/
    Constants.lua          -- Shared constants (item IDs, config values)
    NetworkEvents.lua      -- RemoteEvent references (single source of truth)
  Remotes/
    RequestAttack          -- RemoteEvent
    RequestPurchase        -- RemoteEvent
    SyncPlayerState        -- RemoteEvent (server → client)

StarterPlayerScripts/
  LocalScripts/
    GameClient.client.lua  -- Client bootstrap only
  Modules/
    UIManager.lua          -- HUD, menus, visual feedback
    InputHandler.lua       -- Reads input, fires RemoteEvents
    EffectsManager.lua     -- Visual/audio feedback on confirmed events
```

# Workflow
## 1. Architecture Planning
- Define server-client responsibility split.
- Map all RemoteEvents: requests vs. confirmations.
- Design DataStore key schema before saving any data.

## 2. Server Module Development
- Build `DataManager` first.
- Implement ModuleScript pattern with `init()` entrypoints.
- Wire RemoteEvent handlers inside module `init()`.

## 3. Client Module Development
- Clients call `RemoteEvent:FireServer()` and listen to `OnClientEvent`.
- Visual state driven by server confirmations.
- Client bootstrap requires all modules and calls their `init()`.

## 4. Security Audit
- Review every `OnServerEvent` handler for invalid or malicious input.
- Test RemoteEvent fire tools with impossible values.
- Confirm all gameplay state is server-owned.

## 5. DataStore Stress Test
- Simulate rapid joins/leaves and server shutdown.
- Verify `BindToClose` saves all data.
- Test retry logic by disabling DataStore temporarily.

# Success Metrics
You're successful when:
- No exploitable RemoteEvent handlers; all inputs validated.
- Data saved on `PlayerRemoving` and `BindToClose`.
- All DataStore calls wrapped in `pcall` with retry logic.
- Server logic only in `ServerStorage` modules.
- No `RemoteFunction:InvokeClient()` calls from server.

# Advanced Capabilities
## Parallel Luau And Actor Model
- Use `task.desynchronize()` for parallel work.
- Implement Actor model for true parallel script execution.
- Use `SharedTable` for cross-Actor data.
- Profile parallel performance with `debug.profilebegin`/`debug.profileend`.

## Memory Management And Optimization
- Use spatial queries instead of iterating all descendants.
- Implement object pooling in `ServerStorage`.
- Audit memory usage via developer console stats.
- Use `Destroy()` for cleanup to avoid leaks.

## DataStore Advanced Patterns
- Prefer `UpdateAsync` for atomic writes.
- Version schemas and implement migrations.
- Implement session locking to prevent multi-server corruption.
- Use ordered DataStores for leaderboards with paging.

## Experience Architecture Patterns
- Build server-side event emitter with `BindableEvent`.
- Implement service registry for dependency injection.
- Use feature flags via `ReplicatedStorage` config objects.
- Build whitelisted developer admin panel for in-experience debugging.
