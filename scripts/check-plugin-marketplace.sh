#!/usr/bin/env bash
#
# check-plugin-marketplace.sh — enforce that the plugin marketplace generator
# produces a valid marketplace that stays in sync with the real agent roster.
#
# The source/dist split: the source branch NEVER commits the generated tree.
# scripts/build-marketplace.py emits plugins/ + .claude-plugin/marketplace.json
# into a temp dir, and scripts/publish-marketplace.sh (CI: publish-plugin-
# marketplace.yml) pushes that output to the `plugins` dist branch, which is
# what consumers point @agentPlugins at (<owner>/agency-agents#plugins). So this
# checker validates a FRESH generation into a temp dir, not a committed tree:
#   1. The fresh skill/agent per division exactly matches the source division's
#      frontmatter agent filenames (both directions). Because skills/ and
#      agents/ copies are byte-identical to the source, this also proves sync.
#   2. No legacy <division>/.claude-plugin/plugin.json exists anywhere (the old
#      explicit-`agents`-field design, now ignored at runtime — never return).
#   3. marketplace.json is valid JSON, uses a non-reserved kebab-case name, has
#      owner.name, and lists exactly the divisions in divisions.json in order.
#   4. Every plugin source is ./-prefixed with no "..", resolves to a dir that
#      carries its own .claude-plugin/plugin.json.
#   5. Every plugins/<division>/.claude-plugin/plugin.json is metadata-only (no
#      component path field) because the default-directory layout is contract.
#   6. The source branch is clean of committed generated output: plugins/ and
#      .claude-plugin/marketplace.json must NOT be tracked (they belong only on
#      the `plugins` dist branch). Regression guard against a future commit.
#
# No deps beyond bash 3.2 + coreutils + python3 (already required by
# check-runbooks.sh and check-hermes-plugin.py) so it runs the same on macOS
# and CI. Mirrors scripts/check-divisions.sh. `claude plugin validate` and a
# registration smoke test run separately in CI against a temp build.
#
# Usage: ./scripts/check-plugin-marketplace.sh

set -euo pipefail
cd "$(dirname "$0")/.."

command -v python3 >/dev/null 2>&1 || {
  echo "ERROR: python3 is required for the plugin marketplace check." >&2
  exit 2
}

python3 - <<'PYEOF'
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(os.getcwd())
BUILDER = REPO_ROOT / "scripts" / "build-marketplace.py"

# Reserved marketplace names from the Claude Code plugin-marketplaces docs.
# Claude re-checks these on every marketplace load, so a collision silently
# breaks installs; fail CI instead.
RESERVED_NAMES = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "claude-plugins-community", "claude-community", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
    "knowledge-work-plugins", "life-sciences", "claude-for-legal",
    "claude-for-financial-services", "financial-services-plugins",
    "first-party-plugins", "healthcare",
}

# Component path fields that must NOT appear in plugin.json: the runtime ignores
# explicit component paths in current Claude Code; only the default directories
# (commands/, skills/, agents/) register components.
FORBIDDEN_COMPONENT_FIELDS = (
    "agents", "commands", "skills", "workflows", "hooks", "mcpServers",
    "lspServers", "outputStyles", "experimental",
)

KUBE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("agency_agents_marketplace_builder", BUILDER)
divisions = builder.division_dirs(REPO_ROOT)
expected_plugin = {d: f"agency-{d}" for d in divisions}

errors: list[str] = []
def fail(msg: str) -> None:
    errors.append(msg)
    print(f"  ERROR {msg}")


def rel(p: pathlib.Path) -> str:
    return p.relative_to(REPO_ROOT).as_posix()


# --- 0. Source branch must NOT track generated output (source/dist split) -----
# plugins/ and .claude-plugin/marketplace.json belong only on the `plugins` dist
# branch. If they show up tracked here, a contributor committed the generated
# tree back to the source — fail loudly (that is exactly the bloat we removed).
def tracked(path: str) -> bool:
    r = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path],
        cwd=REPO_ROOT, capture_output=True,
    )
    return r.returncode == 0

if tracked("plugins/"):
    fail("plugins/ is tracked in the source branch — it must live only on the "
         "`plugins` dist branch (git rm -r --cached plugins/ and gitignore it)")
if tracked(".claude-plugin/marketplace.json"):
    fail(".claude-plugin/marketplace.json is tracked in the source branch — it "
         "must live only on the `plugins` dist branch")

# --- 1/2/4. Fresh generation: structure of the temp build ---------------------
# Validate the FRESH output, not a committed tree: because skills/ and agents/
# copies are byte-identical to the source frontmatter, a fresh build comparing
# its own names to the division folder proves content sync without needing the
# generated tree committed.
with tempfile.TemporaryDirectory() as tmp:
    out = pathlib.Path(tmp)
    builder.build(REPO_ROOT, out)

    # Marketplace manifest (fresh).
    generated = out / ".claude-plugin" / "marketplace.json"
    if not generated.exists():
        fail("build did not produce .claude-plugin/marketplace.json")

    # plugins/<division> — every generated skill/agent is byte-identical to its
    # source agent file (the generator guarantees this; assert it so a future
    # generator bug cannot corrupt the published tree undetected). Source agent
    # stems are unique per division (the generator refuses collisions), so a
    # flattened agents/<stem>.md maps to exactly one source file anywhere in the
    # division folder (game-development nests unity/, godot/, ...).
    for division in divisions:
        gen_dir = out / "plugins" / division
        agents_dir = gen_dir / "agents"
        if agents_dir.is_dir():
            for gen_file in agents_dir.glob("*.md"):
                candidates = [p for p in (REPO_ROOT / division).rglob(f"{gen_file.stem}.md")
                              if p.is_file()]
                if not candidates:
                    fail(f"generated agent {gen_file.relative_to(out)} has no source "
                         f"agent file under {division}/")
                    continue
                src = candidates[0]
                if gen_file.read_bytes() != src.read_bytes():
                    fail(f"generated agent {gen_file.relative_to(out)} is not "
                         f"byte-identical to source {rel(src)}")

        # skills/<stem>/SKILL.md — body must equal the source agent body (the
        # frontmatter is a derived name+description wrapper).
        skills_dir = gen_dir / "skills"
        if skills_dir.is_dir():
            for skill_dir in skills_dir.iterdir():
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.is_file():
                    continue
                text = skill_file.read_text(encoding="utf-8").replace("\r\n", "\n")
                if not text.startswith("---\n") or text.count("---\n") < 2:
                    fail(f"generated SKILL.md {rel(skill_file)} is malformed")
                    continue
                generated_body = text.split("---\n", 2)[2]
                candidates = [u for u in (REPO_ROOT / division).rglob(f"{skill_dir.name}.md")
                              if u.is_file()]
                if not candidates:
                    fail(f"generated skill {skill_dir.name} has no source agent file "
                         f"under {division}/")
                    continue
                src_text = candidates[0].read_text(encoding="utf-8").replace("\r\n", "\n")
                src_body = src_text.split("---\n", 2)[2]
                # The generator emits a canonical single trailing newline; some
                # source files lack one. Compare with trailing whitespace
                # normalized so a benign line-ending gap is not a failure while
                # any real content drift still is.
                if generated_body.rstrip("\n") != src_body.rstrip("\n"):
                    fail(f"generated SKILL.md {skill_dir.name} body differs from "
                         f"source {rel(candidates[0])}")

    # Source sync: skills/ and agents/ names == division frontmatter stems.
    for division in divisions:
        source_stems = {p.stem for p in builder.division_agent_files(REPO_ROOT, division)}

        skills_dir = out / "plugins" / division / "skills"
        skill_names = (
            {d.name for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()}
            if skills_dir.is_dir() else set()
        )
        if source_stems != skill_names:
            missing = sorted(source_stems - skill_names)
            extra = sorted(skill_names - source_stems)
            fail(f"plugin '{division}' skills/ out of sync with the division folder "
                 f"(missing: {missing}, extra: {extra})")

        agents_dir = out / "plugins" / division / "agents"
        agent_names = {p.stem for p in agents_dir.glob("*.md")} if agents_dir.is_dir() else set()
        if source_stems != agent_names:
            missing = sorted(source_stems - agent_names)
            extra = sorted(agent_names - source_stems)
            fail(f"plugin '{division}' agents/ out of sync with the division folder "
                 f"(missing: {missing}, extra: {extra})")

    # Marketplace manifest structure (fresh build).
    mp = json.loads(generated.read_text(encoding="utf-8"))
    name = mp.get("name")
    if not (isinstance(name, str) and KUBE_RE.match(name)):
        fail(f"marketplace name must be kebab-case: {name!r}")
    elif name in RESERVED_NAMES:
        fail(f"marketplace name '{name}' is reserved by Claude Code")
    owner = mp.get("owner")
    if not (isinstance(owner, dict) and isinstance(owner.get("name"), str) and owner["name"]):
        fail("marketplace owner.name is required")
    plugins = mp.get("plugins")
    if not isinstance(plugins, list):
        fail("marketplace plugins must be an array")
    else:
        names = [p.get("name") for p in plugins if isinstance(p, dict)]
        want = [expected_plugin[d] for d in divisions]
        if names != want:
            fail(f"marketplace plugin list does not match divisions.json exactly "
                 f"(expected {want}, got {names})")
        for p in plugins:
            if not isinstance(p, dict):
                fail(f"marketplace plugin entry is not an object: {p!r}")
                continue
            src = p.get("source", "")
            if not (isinstance(src, str) and src.startswith("./") and ".." not in src):
                fail(f"plugin '{p.get('name')}' source must be ./-prefixed with no '..': {src}")
                continue
            src_dir = out / src.lstrip("./")
            if not src_dir.is_dir():
                fail(f"plugin '{p.get('name')}' source '{src}' does not exist")
            elif not (src_dir / ".claude-plugin" / "plugin.json").is_file():
                fail(f"plugin '{p.get('name')}' source '{src}' has no .claude-plugin/plugin.json")

    # Per-division plugin.json structure: metadata only (fresh build).
    for d in divisions:
        pj_path = out / "plugins" / d / ".claude-plugin" / "plugin.json"
        if not pj_path.exists():
            fail(f"plugin '{d}' has no .claude-plugin/plugin.json in the build")
            continue
        try:
            pj = json.loads(pj_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"plugin '{d}' plugin.json is not valid JSON: {exc}")
            continue
        if pj.get("name") != expected_plugin[d]:
            fail(f"plugin '{d}' name should be '{expected_plugin[d]}', got '{pj.get('name')}'")
        for field in FORBIDDEN_COMPONENT_FIELDS:
            if field in pj:
                fail(f"plugin '{d}' has a '{field}' component field — the runtime ignores "
                     f"explicit component paths; use the default skills/ and agents/ directories only")

# --- Legacy layout must be gone from the SOURCE division folders ---------------
for division in divisions:
    legacy = REPO_ROOT / division / ".claude-plugin" / "plugin.json"
    if legacy.exists():
        fail(f"legacy {rel(legacy)} still exists — the explicit-`agents`-field layout "
             f"does not register components; delete it and use plugins/")

# --- result ------------------------------------------------------------------
if errors:
    print(f"\nFAILED: {len(errors)} plugin marketplace consistency error(s). "
          f"Run python3 scripts/build-marketplace.py to regenerate.")
    sys.exit(1)
print(f"PASSED: {len(divisions)} division skill plugins consistent across divisions.json, "
      f"the freshly generated build, and the source roster.")
PYEOF
