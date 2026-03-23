# Avante.nvim Integration

> Use Agency agents as custom system prompts in [Avante.nvim](https://github.com/yetone/avante.nvim), the Cursor-like AI coding assistant for Neovim.

## What Is Avante.nvim?

Avante.nvim brings AI-assisted coding to Neovim with inline suggestions, chat, and code generation. It supports custom system prompts, which means you can load Agency agents as personalities.

## Install

### Prerequisites

- Neovim >= 0.10
- [Avante.nvim](https://github.com/yetone/avante.nvim) installed and configured

### Option 1: Copy Agent Files

Copy the agent prompt files from this directory into your Neovim config:

```bash
# Create the prompts directory
mkdir -p ~/.config/nvim/prompts/agency

# Copy all agent prompts
cp integrations/avante/prompts/*.md ~/.config/nvim/prompts/agency/
```

### Option 2: Symlink (Stay Updated)

```bash
ln -s "$(pwd)/integrations/avante/prompts" ~/.config/nvim/prompts/agency
```

## Configuration

Add custom system prompts to your Avante.nvim configuration in `init.lua` or `lazy.nvim` spec:

### lazy.nvim Example

```lua
{
  "yetone/avante.nvim",
  opts = {
    -- Use a specific agent as the default system prompt
    system_prompt = function()
      local f = io.open(vim.fn.expand("~/.config/nvim/prompts/agency/senior-developer.md"), "r")
      if f then
        local content = f:read("*a")
        f:close()
        return content
      end
      return ""
    end,
  },
}
```

### Switch Agents Dynamically

Create a Neovim command to switch agents on the fly:

```lua
-- Add to your init.lua
vim.api.nvim_create_user_command("AvanteAgent", function(opts)
  local agent_name = opts.args
  local path = vim.fn.expand("~/.config/nvim/prompts/agency/" .. agent_name .. ".md")
  local f = io.open(path, "r")
  if f then
    local content = f:read("*a")
    f:close()
    -- Update avante system prompt
    require("avante.config").override({ system_prompt = content })
    vim.notify("Loaded agent: " .. agent_name, vim.log.levels.INFO)
  else
    vim.notify("Agent not found: " .. agent_name, vim.log.levels.ERROR)
  end
end, {
  nargs = 1,
  complete = function()
    local agents = {}
    local dir = vim.fn.expand("~/.config/nvim/prompts/agency/")
    for _, file in ipairs(vim.fn.glob(dir .. "*.md", false, true)) do
      table.insert(agents, vim.fn.fnamemodify(file, ":t:r"))
    end
    return agents
  end,
})
```

Usage:

```
:AvanteAgent senior-developer
:AvanteAgent code-reviewer
:AvanteAgent rapid-prototyper
```

## Included Agent Prompts

| File | Agent | Best For |
|------|-------|----------|
| `senior-developer.md` | Senior Developer | Complex implementations, architecture |
| `code-reviewer.md` | Code Reviewer | PR reviews, code quality |
| `rapid-prototyper.md` | Rapid Prototyper | Fast POCs, MVPs |
| `frontend-developer.md` | Frontend Developer | UI work, React/Vue/Angular |
| `security-engineer.md` | Security Engineer | Security audits, threat modeling |

## Adding More Agents

Any agent from The Agency can be used with Avante.nvim. To convert one:

1. Open the agent file from the repo (e.g., `engineering/engineering-backend-architect.md`)
2. Remove the YAML frontmatter (`---` block at the top)
3. Save it to `~/.config/nvim/prompts/agency/backend-architect.md`

Or copy the full file — Avante.nvim will ignore the frontmatter.

## Tips

- **Keep prompts focused**: Avante.nvim works best with concise system prompts. The included files are trimmed versions optimized for coding assistance.
- **Project-local agents**: Place agent files in `.avante/prompts/` in your project root for project-specific agents.
- **Combine with Avante's features**: Use agents alongside Avante's inline editing, chat, and code generation for best results.
