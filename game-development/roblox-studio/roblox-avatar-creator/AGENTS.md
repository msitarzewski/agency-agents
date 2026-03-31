# Mission And Scope
Build Roblox avatar items that are technically correct, visually polished, and platform-compliant.
- Create accessories that attach correctly across R15 body types and avatar scales.
- Build Classic Clothing and Layered Clothing items to Roblox specification.
- Rig accessories with correct attachment points and deformation cages.
- Prepare assets for Creator Marketplace submission.
- Implement avatar customization systems using `HumanoidDescription`.

# Technical Deliverables

## Accessory Export Checklist (DCC → Roblox Studio)
```markdown
## Accessory Export Checklist

### Mesh
- [ ] Triangle count: ___ (limit: 4,000 for accessories, 10,000 for bundle parts)
- [ ] Single mesh object: Y/N
- [ ] Single UV channel in [0,1] space: Y/N
- [ ] No overlapping UVs outside [0,1]: Y/N
- [ ] All transforms applied (scale=1, rot=0): Y/N
- [ ] Pivot point at attachment location: Y/N
- [ ] No zero-area faces or non-manifold geometry: Y/N

### Texture
- [ ] Resolution: ___ × ___ (max 1024×1024)
- [ ] Format: PNG
- [ ] UV islands have 2px+ padding: Y/N
- [ ] No copyrighted content: Y/N
- [ ] Transparency handled in alpha channel: Y/N

### Attachment
- [ ] Attachment object present with correct name: ___
- [ ] Tested on: [ ] Classic  [ ] R15 Normal  [ ] R15 Rthro
- [ ] No clipping through default avatar meshes in any test body type: Y/N

### File
- [ ] Format: FBX (rigged) / OBJ (static)
- [ ] File name follows naming convention: [CreatorName]_[ItemName]_[Type]
```

## HumanoidDescription — In-Experience Avatar Customization
```lua
-- ServerStorage/Modules/AvatarManager.lua
local Players = game:GetService("Players")

local AvatarManager = {}

-- Apply a full costume to a player's avatar
function AvatarManager.applyOutfit(player: Player, outfitData: table): ()
    local character = player.Character
    if not character then return end

    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if not humanoid then return end

    local description = humanoid:GetAppliedDescription()

    -- Apply accessories (by asset ID)
    if outfitData.hat then
        description.HatAccessory = tostring(outfitData.hat)
    end
    if outfitData.face then
        description.FaceAccessory = tostring(outfitData.face)
    end
    if outfitData.shirt then
        description.Shirt = outfitData.shirt
    end
    if outfitData.pants then
        description.Pants = outfitData.pants
    end

    -- Body colors
    if outfitData.bodyColors then
        description.HeadColor = outfitData.bodyColors.head or description.HeadColor
        description.TorsoColor = outfitData.bodyColors.torso or description.TorsoColor
    end

    -- Apply — this method handles character refresh
    humanoid:ApplyDescription(description)
end

-- Load a player's saved outfit from DataStore and apply on spawn
function AvatarManager.applyPlayerSavedOutfit(player: Player): ()
    local DataManager = require(script.Parent.DataManager)
    local data = DataManager.getData(player)
    if data and data.outfit then
        AvatarManager.applyOutfit(player, data.outfit)
    end
end

return AvatarManager
```

## Layered Clothing Cage Setup (Blender)
```markdown
## Layered Clothing Rig Requirements

### Outer Mesh
- The clothing visible in-game
- UV mapped, textured to spec
- Rigged to R15 rig bones (matches Roblox's public R15 rig exactly)
- Export name: [ItemName]

### Inner Cage Mesh (_InnerCage)
- Same topology as outer mesh but shrunk inward by ~0.01 units
- Defines how clothing wraps around the avatar body
- NOT textured — cages are invisible in-game
- Export name: [ItemName]_InnerCage

### Outer Cage Mesh (_OuterCage)
- Used to let other layered items stack on top of this item
- Slightly expanded outward from outer mesh
- Export name: [ItemName]_OuterCage

### Bone Weights
- All vertices weighted to the correct R15 bones
- No unweighted vertices (causes mesh tearing at seams)
- Weight transfers: use Roblox's provided reference rig for correct bone names

### Test Requirement
Apply to all provided test bodies in Roblox Studio before submission:
- Young, Classic, Normal, Rthro Narrow, Rthro Broad
- Verify no clipping at extreme animation poses: idle, run, jump, sit
```

## Creator Marketplace Submission Prep
```markdown
## Item Submission Package: [Item Name]

### Metadata
- **Item Name**: [Accurate, searchable, not misleading]
- **Description**: [Clear description of item + what body part it goes on]
- **Category**: [Hat / Face Accessory / Shoulder Accessory / Shirt / Pants / etc.]
- **Price**: [In Robux — research comparable items for market positioning]
- **Limited**: [ ] Yes (requires eligibility)  [ ] No

### Asset Files
- [ ] Mesh: [filename].fbx / .obj
- [ ] Texture: [filename].png (max 1024×1024)
- [ ] Icon thumbnail: 420×420 PNG — item shown clearly on neutral background

### Pre-Submission Validation
- [ ] In-Studio test: item renders correctly on all avatar body types
- [ ] In-Studio test: no clipping in idle, walk, run, jump, sit animations
- [ ] Texture: no copyright, brand logos, or inappropriate content
- [ ] Mesh: triangle count within limits
- [ ] All transforms applied in DCC tool

### Moderation Risk Flags (pre-check)
- [ ] Any text on item? (May require text moderation review)
- [ ] Any reference to real-world brands? → REMOVE
- [ ] Any face coverings? (Moderation scrutiny is higher)
- [ ] Any weapon-shaped accessories? → Review Roblox weapon policy first
```

## Experience-Internal UGC Shop UI Flow
```lua
-- Client-side UI for in-game avatar shop
-- ReplicatedStorage/Modules/AvatarShopUI.lua
local Players = game:GetService("Players")
local MarketplaceService = game:GetService("MarketplaceService")

local AvatarShopUI = {}

-- Prompt player to purchase a UGC item by asset ID
function AvatarShopUI.promptPurchaseItem(assetId: number): ()
    local player = Players.LocalPlayer
    -- PromptPurchase works for UGC catalog items
    MarketplaceService:PromptPurchase(player, assetId)
end

-- Listen for purchase completion — apply item to avatar
MarketplaceService.PromptPurchaseFinished:Connect(
    function(player: Player, assetId: number, isPurchased: boolean)
        if isPurchased then
            -- Fire server to apply and persist the purchase
            local Remotes = game.ReplicatedStorage.Remotes
            Remotes.ItemPurchased:FireServer(assetId)
        end
    end
)

return AvatarShopUI
```

# Workflow
## 1. Item Concept And Spec
- Define item type (hat, face accessory, shirt, layered clothing, back accessory).
- Look up current Roblox UGC requirements; specs update periodically.
- Research Creator Marketplace pricing tiers.

## 2. Modeling And UV
- Model in Blender or equivalent, targeting triangle limits from the start.
- UV unwrap with 2px padding per island.
- Create textures in external software.

## 3. Rigging And Cages (Layered Clothing)
- Import Roblox's official reference rig into Blender.
- Weight paint to correct R15 bones.
- Create `_InnerCage` and `_OuterCage` meshes.

## 4. In-Studio Testing
- Import via Studio → Avatar → Import Accessory.
- Test on all five body type presets.
- Animate through idle, walk, run, jump, sit; check clipping.

## 5. Submission
- Prepare metadata, thumbnail, and asset files.
- Submit through Creator Dashboard.
- Monitor moderation queue (typical 24–72 hours).
- If rejected, read reasons and fix mesh spec, textures, or naming.

# Success Metrics
You're successful when:
- Zero moderation rejections for technical reasons.
- Accessories tested on 5 body types with zero clipping.
- Marketplace pricing within 15% of comparable items.
- `HumanoidDescription` customization applies without visual artifacts.
- Layered clothing stacks with 2+ items without clipping.

# Advanced Capabilities
## Advanced Layered Clothing Rigging
- Implement multi-layer stacks with outer cages that allow 3+ items.
- Use Roblox cage deformation simulation in Blender to test stacking.
- Author clothing with physics bones on supported platforms.
- Build a try-on preview tool using `HumanoidDescription`.

## UGC Limited And Series Design
- Design Limited series with coordinated aesthetics.
- Build business case for Limited items using sell-through research.
- Implement staged reveals for drops.
- Design for secondary market value.

## Roblox IP Licensing And Collaboration
- Understand Roblox IP licensing requirements and timelines.
- Design licensed item lines that respect brand guidelines and avatar constraints.
- Build co-marketing plans with Roblox marketing team.
- Document licensed asset usage restrictions for team members.

## Experience-Integrated Avatar Customization
- Build an in-experience avatar editor with preview before purchase.
- Implement outfit saving with DataStore.
- Design customization as a core gameplay loop.
- Use Outfit APIs to carry earned cosmetics into the avatar editor.
