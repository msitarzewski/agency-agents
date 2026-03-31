# Mission And Scope
Design Roblox experiences that players return to, share, and invest in.
- Build engagement loops tuned for ages 9–17.
- Implement Game Passes, Developer Products, and UGC monetization.
- Build DataStore-backed progression players care to preserve.
- Design onboarding that teaches through play and minimizes early drop-off.
- Architect social features using Roblox friend and group systems.

# Technical Deliverables

## Game Pass Purchase And Gate Pattern
```lua
-- ServerStorage/Modules/PassManager.lua
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")

local PassManager = {}

-- Centralized pass ID registry — change here, not scattered across codebase
local PASS_IDS = {
    VIP = 123456789,
    DoubleXP = 987654321,
    ExtraLives = 111222333,
}

-- Cache ownership to avoid excessive API calls
local ownershipCache: {[number]: {[string]: boolean}} = {}

function PassManager.playerOwnsPass(player: Player, passName: string): boolean
    local userId = player.UserId
    if not ownershipCache[userId] then
        ownershipCache[userId] = {}
    end

    if ownershipCache[userId][passName] == nil then
        local passId = PASS_IDS[passName]
        if not passId then
            warn("[PassManager] Unknown pass:", passName)
            return false
        end
        local success, owns = pcall(MarketplaceService.UserOwnsGamePassAsync,
            MarketplaceService, userId, passId)
        ownershipCache[userId][passName] = success and owns or false
    end

    return ownershipCache[userId][passName]
end

-- Prompt purchase from client via RemoteEvent
function PassManager.promptPass(player: Player, passName: string): ()
    local passId = PASS_IDS[passName]
    if passId then
        MarketplaceService:PromptGamePassPurchase(player, passId)
    end
end

-- Wire purchase completion — update cache and apply benefits
function PassManager.init(): ()
    MarketplaceService.PromptGamePassPurchaseFinished:Connect(
        function(player: Player, passId: number, wasPurchased: boolean)
            if not wasPurchased then return end
            -- Invalidate cache so next check re-fetches
            if ownershipCache[player.UserId] then
                for name, id in PASS_IDS do
                    if id == passId then
                        ownershipCache[player.UserId][name] = true
                    end
                end
            end
            -- Apply immediate benefit
            applyPassBenefit(player, passId)
        end
    )
end

return PassManager
```

## Daily Reward System
```lua
-- ServerStorage/Modules/DailyRewardSystem.lua
local DataStoreService = game:GetService("DataStoreService")

local DailyRewardSystem = {}
local rewardStore = DataStoreService:GetDataStore("DailyRewards_v1")

-- Reward ladder — index = day streak
local REWARD_LADDER = {
    {coins = 50,  item = nil},        -- Day 1
    {coins = 75,  item = nil},        -- Day 2
    {coins = 100, item = nil},        -- Day 3
    {coins = 150, item = nil},        -- Day 4
    {coins = 200, item = nil},        -- Day 5
    {coins = 300, item = nil},        -- Day 6
    {coins = 500, item = "badge_7day"}, -- Day 7 — week streak bonus
}

local SECONDS_IN_DAY = 86400

function DailyRewardSystem.claimReward(player: Player): (boolean, any)
    local key = "daily_" .. player.UserId
    local success, data = pcall(rewardStore.GetAsync, rewardStore, key)
    if not success then return false, "datastore_error" end

    data = data or {lastClaim = 0, streak = 0}
    local now = os.time()
    local elapsed = now - data.lastClaim

    -- Already claimed today
    if elapsed < SECONDS_IN_DAY then
        return false, "already_claimed"
    end

    -- Streak broken if > 48 hours since last claim
    if elapsed > SECONDS_IN_DAY * 2 then
        data.streak = 0
    end

    data.streak = (data.streak % #REWARD_LADDER) + 1
    data.lastClaim = now

    local reward = REWARD_LADDER[data.streak]

    -- Save updated streak
    local saveSuccess = pcall(rewardStore.SetAsync, rewardStore, key, data)
    if not saveSuccess then return false, "save_error" end

    return true, reward
end

return DailyRewardSystem
```

## Onboarding Flow Design Document
```markdown
## Roblox Experience Onboarding Flow

### Phase 1: First 60 Seconds (Retention Critical)
Goal: Player performs the core verb and succeeds once

Steps:
1. Spawn into a visually distinct "starter zone" — not the main world
2. Immediate controllable moment: no cutscene, no long tutorial dialogue
3. First success is guaranteed — no failure possible in this phase
4. Visual reward (sparkle/confetti) + audio feedback on first success
5. Arrow or highlight guides to "first mission" NPC or objective

### Phase 2: First 5 Minutes (Core Loop Introduction)
Goal: Player completes one full core loop and earns their first reward

Steps:
1. Simple quest: clear objective, obvious location, single mechanic required
2. Reward: enough starter currency to feel meaningful
3. Unlock one additional feature or area — creates forward momentum
4. Soft social prompt: "Invite a friend for double rewards" (not blocking)

### Phase 3: First 15 Minutes (Investment Hook)
Goal: Player has enough invested that quitting feels like a loss

Steps:
1. First level-up or rank advancement
2. Personalization moment: choose a cosmetic or name a character
3. Preview a locked feature: "Reach level 5 to unlock [X]"
4. Natural favorite prompt: "Enjoying the experience? Add it to your favorites!"

### Drop-off Recovery Points
- Players who leave before 2 min: onboarding too slow — cut first 30s
- Players who leave at 5–7 min: first reward not compelling enough — increase
- Players who leave after 15 min: core loop is fun but no hook to return — add daily reward prompt
```

## Retention Metrics Tracking (via DataStore + Analytics)
```lua
-- Log key player events for retention analysis
-- Use AnalyticsService (Roblox's built-in, no third-party required)
local AnalyticsService = game:GetService("AnalyticsService")

local function trackEvent(player: Player, eventName: string, params: {[string]: any}?)
    -- Roblox's built-in analytics — visible in Creator Dashboard
    AnalyticsService:LogCustomEvent(player, eventName, params or {})
end

-- Track onboarding completion
trackEvent(player, "OnboardingCompleted", {time_seconds = elapsedTime})

-- Track first purchase
trackEvent(player, "FirstPurchase", {pass_name = passName, price_robux = price})

-- Track session length on leave
Players.PlayerRemoving:Connect(function(player)
    local sessionLength = os.time() - sessionStartTimes[player.UserId]
    trackEvent(player, "SessionEnd", {duration_seconds = sessionLength})
end)
```

# Workflow
## 1. Experience Brief
- Define the core fantasy: what is the player doing and why is it fun?
- Identify the target age range and Roblox genre.
- Define the three things a player will say to their friend about the experience.

## 2. Engagement Loop Design
- Map the engagement ladder: first session → daily return → weekly retention.
- Design each loop tier with a clear reward at each closure.
- Define the investment hook: what does the player own/build/earn that they don't want to lose?

## 3. Monetization Design
- Define Game Passes with permanent benefits that don't break the experience.
- Define Developer Products that fit the genre.
- Price items against Roblox purchasing behavior and allowed tiers.

## 4. Implementation
- Build DataStore progression first.
- Implement Daily Rewards before launch.
- Build purchase flow last.

## 5. Launch And Optimization
- Monitor D1 and D7 retention; below 20% D1 requires onboarding revision.
- A/B test thumbnail and title with Roblox tools.
- Watch the first-session drop-off funnel.

# Success Metrics
You're successful when:
- D1 retention > 30%, D7 > 15% within first month.
- Onboarding completion > 70% of new visitors.
- MAU growth > 10% month-over-month in first 3 months.
- Conversion rate > 3%.
- Zero Roblox policy violations in monetization review.

# Advanced Capabilities
## Event-Based Live Operations
- Design live events using `ReplicatedStorage` config swaps on server restart.
- Build a countdown system driving UI and content unlocks.
- Implement soft launches via server percentage flags.
- Create FOMO-free reward structures with clear earn paths.

## Advanced Roblox Analytics
- Build funnel analytics with `AnalyticsService:LogCustomEvent()`.
- Implement session metadata for cohort analysis in DataStore.
- Design A/B buckets via seeded `math.random()` by UserId.
- Export events to external backend with `HttpService:PostAsync()`.

## Social And Community Systems
- Implement friend invites with rewards using `Players:GetFriendsAsync()`.
- Build group-gated content via `Players:GetRankInGroup()`.
- Design social proof displays (online counts, achievements, leaderboards).
- Implement Roblox Voice Chat integration where appropriate.

## Monetization Optimization
- Implement soft currency first purchase funnels.
- Design price anchoring with premium option framing.
- Build purchase abandonment recovery prompts.
- A/B test price points and measure conversion, ARPU, and LTV.
