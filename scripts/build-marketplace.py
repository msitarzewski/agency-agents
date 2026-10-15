#!/usr/bin/env python3
"""Build the Claude-format plugin marketplace for The Agency agents.

The Agency's source agents live as flat frontmatter .md files inside top-level
division directories (engineering/, marketing/, ...), with divisions.json as the
single source of truth for the division set. This script publishes those
specialists WITHOUT moving, renaming, or editing any source file. It emits one
plugin per division at plugins/<division>/, using ONLY default-directory layout
(no explicit component path fields in plugin.json, which the runtime ignores):

  * skills/<stem>/SKILL.md — each specialist as a portable Agent Skill. The
    SKILL frontmatter carries `name: <stem>` (kebab-case, identical to the skill
    directory name, as VS Code Agent Plugins requires) plus the source
    `description`; the body is the source agent body verbatim. This is the one
    primitive that registers across every consumer: VS Code Agent Plugins,
    Claude Code, Claude Desktop, and GitHub Copilot CLI.
  * agents/<stem>.md — a byte-identical copy of the source agent file, so the
    same specialist is ALSO usable as a Claude Code sub-agent (isolated context).
    VS Code Agent Plugins 1.0 ignores the agents/ directory; this is harmless
    there and adds the sub-agent surface for Claude Code with no source edits.
  * README.md — a generated per-plugin readme. VS Code's plugin detail pane
    fetches this file; without it the detail view renders "404: Not Found".
  * .claude-plugin/plugin.json — identity metadata only. No agents/commands/
    skills path fields: default-directory discovery is the contract.

A marketplace registry at .claude-plugin/marketplace.json lists all divisions
with sources ./plugins/<division>.

The generated plugins/ tree MUST be committed: consumers clone this repo and
read it directly -- no build step runs on install. scripts/check-plugin-
marketplace.sh (CI: check-plugin-marketplace.yml) fails the build if the
committed output drifts from what this script produces or from the source agent
files. Version is deliberately omitted from every manifest so Claude Code
versions each plugin by git commit SHA.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

MARKETPLACE_NAME = "agency-agents"
PLUGIN_PREFIX = "agency-"
# Skill/agent directory + file names come from the source filename stem, which
# must be plain kebab-case: VS Code requires the skill directory name to equal a
# kebab-case `name` in SKILL.md frontmatter.
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def division_dirs(repo_root: Path) -> list[str]:
    # divisions.json (repo root) is the single source of truth for the division
    # set. Read it rather than hardcoding a copy here: a hardcoded list silently
    # drops new divisions the moment the catalog grows. check-divisions.sh
    # guards divisions.json against the tracked dirs, so deriving from it keeps
    # this plugin in sync by construction.
    data = json.loads((repo_root / "divisions.json").read_text(encoding="utf-8"))
    return sorted(data["divisions"].keys())


def division_label(repo_root: Path, division: str) -> str:
    data = json.loads((repo_root / "divisions.json").read_text(encoding="utf-8"))
    return data["divisions"][division]["label"]


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str] | None:
    # Same effective gate as convert.sh: a .md whose first line is `---`
    # frontmatter, carrying a non-empty `name`. Returns ({name, description,
    # ...}, body) or None for files that are not specialists (e.g. per-division
    # docs with no frontmatter). Frontmatter here is flat `key: value` lines;
    # that is all the source agents use.
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return None
    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    if not fields.get("name"):
        return None
    return fields, parts[2]


def is_agent_file(path: Path) -> bool:
    return parse_frontmatter(path) is not None


def division_agent_files(repo_root: Path, division: str) -> list[Path]:
    base = repo_root / division
    return sorted(path for path in base.rglob("*.md") if is_agent_file(path))


def yaml_double_quote(value: str) -> str:
    # Emit a YAML double-quoted scalar so descriptions containing ": ", "#", or
    # quotes stay valid regardless of content. Deterministic, so the drift check
    # stays byte-stable.
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def skill_markdown(stem: str, description: str, body: str) -> bytes:
    # A portable Agent Skill: `name` MUST equal the skill directory name
    # (kebab-case) for VS Code Agent Plugins; `description` drives auto-invocation
    # everywhere. Body is the source agent body verbatim. LF endings + trailing
    # newline so the drift check is byte-stable on every platform.
    front = f"---\nname: {stem}\ndescription: {yaml_double_quote(description)}\n---\n"
    text = front + body
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def plugin_readme(repo_root: Path, division: str, specialists: list[tuple[str, str, str]]) -> bytes:
    # VS Code's plugin detail pane fetches plugins/<division>/README.md; a missing
    # file renders "404: Not Found" there. Content is derived from the roster so
    # it stays byte-stable (no timestamps).
    label = division_label(repo_root, division)
    plugin_name = f"{PLUGIN_PREFIX}{division}"
    lines = [
        f"# Agency — {label}",
        "",
        f"The Agency {label} division, packaged as installable Agent Skills for "
        "VS Code Agent Plugins, Claude Code, Claude Desktop, and GitHub Copilot "
        "CLI. Each specialist is also available as a Claude Code sub-agent.",
        "",
        f"## Specialists ({len(specialists)})",
        "",
    ]
    for stem, display_name, description in specialists:
        lines.append(f"- **{display_name}** (`{stem}`) — {description}")
    lines += [
        "",
        "## Usage",
        "",
        "Install the division, then invoke a specialist by describing the task or "
        "with its slash command:",
        "",
        "```text",
        f"/{plugin_name}:{specialists[0][0]}",
        "```",
        "",
        "In VS Code the specialists appear as skills in chat once the plugin is "
        "enabled; in Claude Code they are available both as skills and as "
        "sub-agents.",
        "",
    ]
    return ("\n".join(lines)).encode("utf-8")


def plugin_json(repo_root: Path, division: str, count: int) -> dict[str, object]:
    noun = "skill" if count == 1 else "skills"
    return {
        "name": f"{PLUGIN_PREFIX}{division}",
        "displayName": f"Agency — {division_label(repo_root, division)}",
        "description": (
            f"The Agency {division_label(repo_root, division)} division: "
            f"{count} specialist {noun}."
        ),
        "author": {"name": "Agency Agents"},
    }


def marketplace_json(repo_root: Path, counts: dict[str, int]) -> dict[str, object]:
    divisions = division_dirs(repo_root)
    plugins = []
    for division in divisions:
        count = counts[division]
        noun = "skill" if count == 1 else "skills"
        plugins.append({
            "name": f"{PLUGIN_PREFIX}{division}",
            "source": f"./plugins/{division}",
            "description": (
                f"{division_label(repo_root, division)} division "
                f"({count} specialist {noun})"
            ),
        })
    return {
        "name": MARKETPLACE_NAME,
        "description": (
            f"The Agency — {len(divisions)} installable agent divisions for "
            "Claude Code, VS Code, Claude Desktop, and GitHub Copilot CLI"
        ),
        "owner": {"name": "Agency Agents"},
        "plugins": plugins,
    }


def write_json(path: Path, obj: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # write_bytes keeps the output LF on every platform (on Windows, text-mode
    # writes would translate \n to \r\n and break the byte-identity drift check)
    # and works on Python 3.9+, which lacks write_text's newline parameter.
    path.write_bytes(
        (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )


def remove_legacy_division_manifests(repo_root: Path, out_dir: Path) -> None:
    # The first design put a .claude-plugin/plugin.json inside each division
    # folder using the explicit `agents` field, which current Claude Code ignores
    # at runtime. Remove those marketplace-owned artifacts so a regeneration
    # fully converges on the plugins/ layout.
    for division in division_dirs(repo_root):
        legacy = out_dir / division / ".claude-plugin"
        if legacy.is_dir():
            shutil.rmtree(legacy)


def build(repo_root: Path, out_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    remove_legacy_division_manifests(repo_root, out_dir)
    plugins_root = out_dir / "plugins"
    divisions = division_dirs(repo_root)

    # Drop orphaned plugin dirs for divisions that no longer exist, so removing
    # a division from divisions.json cannot leave a stale committed plugin.
    if plugins_root.is_dir():
        for entry in plugins_root.iterdir():
            if entry.is_dir() and entry.name not in divisions:
                shutil.rmtree(entry)

    for division in divisions:
        agents = division_agent_files(repo_root, division)
        if not agents:
            raise SystemExit(
                f"division '{division}' has no frontmatter agent files — "
                "refusing to emit an empty plugin"
            )
        # Skill/agent names come from the filename stem, which must be unique
        # within a division (e.g. game-development/unity/unity-architect.md ->
        # skills/unity-architect/) and plain kebab-case (VS Code requirement).
        stems = [path.stem for path in agents]
        dupes = sorted({s for s in stems if stems.count(s) > 1})
        if dupes:
            raise SystemExit(
                f"division '{division}' has duplicate agent basenames that "
                f"would collide as skill/agent names: {', '.join(dupes)}"
            )
        bad = sorted(s for s in stems if not KEBAB_RE.match(s))
        if bad:
            raise SystemExit(
                f"division '{division}' has non-kebab-case agent filenames that "
                f"cannot be skill names: {', '.join(bad)}"
            )
        counts[division] = len(agents)

        plugin_dir = plugins_root / division
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)

        specialists: list[tuple[str, str, str]] = []
        for agent in agents:
            parsed = parse_frontmatter(agent)
            assert parsed is not None  # is_agent_file already filtered
            fields, body = parsed
            stem = agent.stem
            description = fields.get("description", "").strip()
            if not description:
                raise SystemExit(
                    f"agent '{agent}' has no description — required for a skill"
                )
            display_name = fields["name"].strip()

            # Portable skill (registers in every consumer).
            skill_dir = plugin_dir / "skills" / stem
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_bytes(
                skill_markdown(stem, description, body)
            )

            # Byte-identical sub-agent copy (Claude Code only; VS Code ignores it).
            agents_dir = plugin_dir / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(agent, agents_dir / f"{stem}.md")

            specialists.append((stem, display_name, description))

        (plugin_dir / "README.md").write_bytes(
            plugin_readme(repo_root, division, specialists)
        )
        write_json(
            plugin_dir / ".claude-plugin" / "plugin.json",
            plugin_json(repo_root, division, len(agents)),
        )

    write_json(
        out_dir / ".claude-plugin" / "marketplace.json",
        marketplace_json(repo_root, counts),
    )
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: parent of this script)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory; default is the repo root (write in place)",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = (args.out or repo_root).resolve()
    counts = build(repo_root, out_dir)
    total = sum(counts.values())
    print(
        f"wrote .claude-plugin/marketplace.json + {len(counts)} division "
        f"plugins ({total} specialists as skills + sub-agents) to {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
