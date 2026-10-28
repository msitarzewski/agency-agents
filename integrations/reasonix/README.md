# Reasonix

Convert Agency personas into [Reasonix](https://github.com/esengine/DeepSeek-Reasonix)
manual subagent profiles, rather than inline skills:

```bash
./scripts/convert.sh --tool reasonix
./scripts/install.sh --tool reasonix
# Or install into a project, from its root:
/path/to/agency-agents/scripts/install.sh --tool reasonix --path .reasonix/skills
```

Each `reasonix-agency-<name-slug>/SKILL.md` keeps the original description and
complete persona, with `invocation: manual` and `runAs: subagent`. For example,
`/reasonix-agency-frontend-developer` selects the frontend profile. No model,
effort or tool permissions are overridden. Profile names are lowercase ASCII
and at most 64 characters; an oversized name fails before output is cleaned.

The `reasonix-agency-` namespace allows these profiles to coexist with inline
Agency skills (`agency-<slug>`) installed by Antigravity. Reasonix gives project
skills precedence over global ones, so reusing inline names would hide global
subagent profiles in those projects.

Destination precedence is `--path`, then `REASONIX_SKILLS_DIR`, then
`$REASONIX_HOME/skills`, then the native default: `~/.reasonix/skills` on
macOS/Linux, or `%APPDATA%/reasonix/skills` on Windows (with the user-profile
AppData/Roaming fallback). `REASONIX_SKILLS_DIR` is an Agency installer override.
Environment paths must be absolute or begin with `~/`; use `--path` for a
project-relative destination. Git Bash/MSYS/Cygwin requires `cygpath` for native
Windows paths, otherwise use `--path`. WSL follows the Linux location.

Use the normal `--agent`, `--division`, `--agents-file`, `--dry-run`, `--link`
and `--no-convert` options. Generate profiles locally; never commit them.
