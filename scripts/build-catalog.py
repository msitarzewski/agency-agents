#!/usr/bin/env python3
"""Build the static, searchable agent catalog (GitHub Pages).

Reads every agent in the division directories listed in divisions.json and
writes two files into a gitignored build directory (default: _site/):

  agents.json  the catalog index (one entry per agent, plus build metadata)
  index.html   site/index.html with that same index inlined, so the page is a
               single request and works when opened straight from disk

Standard library only, so it runs as `python3 scripts/build-catalog.py` in CI
and `py scripts/build-catalog.py` on Windows without installing anything.

What counts as an agent is the definition the rest of the repo already uses:
  * divisions come from divisions.json (build-hermes-plugin.py division_dirs;
    check-divisions.sh keeps that file in step with the directories on disk);
  * every *.md under a division directory, recursively, is linted as an agent
    (scripts/lint-agents.sh) and must open with a `---` frontmatter fence
    (lib.sh is_agent_file). A .md there without one is an error here too,
    exactly as it is for the linter, so the catalog count always equals the
    linter's "in N files" count.

Frontmatter is read the way build-hermes-plugin.py parse_agent reads it
(top-level `key: value` lines, no YAML dependency), with the two refinements
lib.sh get_field makes for the converters and install.sh: one matching pair
of outer quotes is a delimiter (not content), and a plain scalar continued on
indented lines is folded into one line. Without the folding, multi-line
descriptions (healthcare-clinical-evidence-agent.md) are cut at the first line.

Two slugs are recorded per agent:
  slug          the filename stem, unique across the repo (URL/anchor id)
  install_slug  slugify(name), which is what `install.sh --agent` matches
                (lib.sh agent_slug) and differs from the stem for most agents

Usage:
  build-catalog.py [--out DIR] [--repo-url URL]   build the site
  build-catalog.py --check                        validate only, write nothing
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_URL = "https://github.com/msitarzewski/agency-agents/blob/main/"
TEMPLATE_REL = Path("site") / "index.html"
DATA_PLACEHOLDER = "{{CATALOG_JSON}}"
CSP_PLACEHOLDER = "{{CSP}}"

# name/description/color are what lint-agents.sh requires; the catalog card
# also needs an emoji. vibe is optional (one agent has none) and renders only
# when present.
REQUIRED_FIELDS = ("name", "description", "color", "emoji")
OPTIONAL_FIELDS = ("vibe",)
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
TOP_LEVEL_KEY = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")


class CatalogError(Exception):
    """A problem that must fail the build (and --check)."""


# ---------------------------------------------------------------------------
# Agent discovery and parsing
# ---------------------------------------------------------------------------


def load_divisions(repo_root: Path) -> dict[str, dict[str, str]]:
    """divisions.json -> {division: {label, icon, color}}, validated."""
    data = json.loads((repo_root / "divisions.json").read_text(encoding="utf-8"))
    divisions = data.get("divisions")
    if not isinstance(divisions, dict) or not divisions:
        raise CatalogError('divisions.json has no "divisions" object')
    problems = []
    for key, meta in divisions.items():
        if not re.fullmatch(r"[a-z0-9-]+", key):
            problems.append(f"division key {key!r} is not a lowercase directory name")
        if not isinstance(meta, dict):
            problems.append(f"division {key!r} is not an object")
            continue
        for field in ("label", "icon", "color"):
            if not isinstance(meta.get(field), str) or not meta[field].strip():
                problems.append(f"division {key!r} is missing {field!r}")
        # The page puts this color into a CSS custom property, so only a plain
        # hex value is accepted.
        if isinstance(meta.get("color"), str) and not HEX_COLOR.match(meta["color"]):
            problems.append(f"division {key!r} color {meta['color']!r} is not #RRGGBB")
    if problems:
        raise CatalogError("divisions.json: " + "; ".join(problems))
    return {k: divisions[k] for k in sorted(divisions)}


def slugify(value: str) -> str:
    """Same result as lib.sh slugify (and build-hermes-plugin.py slugify)."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _unquote(value: str) -> str:
    """lib.sh get_field emit(): trim, then strip one matching outer quote pair."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Top-level frontmatter fields, or None if the file has no frontmatter."""
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    fields: dict[str, str] = {}
    current: str | None = None
    for line in lines[1:end]:
        match = TOP_LEVEL_KEY.match(line)
        if match:
            key, value = match.group(1), match.group(2)
            if key in fields:  # first match wins, as in get_field
                current = None
                continue
            fields[key] = value
            current = key
        elif current and line[:1] in (" ", "\t") and line.strip():
            # Indented continuation of a plain scalar: fold with one space.
            # (For block values such as `services:` this collects the nested
            # lines, but those keys are never read.)
            fields[current] = (fields[current].rstrip() + " " + line.strip()).strip()
        else:
            current = None
    return {k: _unquote(v) for k, v in fields.items()}


def agent_files(repo_root: Path, divisions: dict) -> list[Path]:
    """Every *.md under each division dir, recursively — the linter's file set."""
    files: list[Path] = []
    for division in divisions:
        base = repo_root / division
        if base.is_dir():
            files.extend(p for p in base.rglob("*.md") if p.is_file())
    return sorted(files, key=lambda p: p.relative_to(repo_root).as_posix())


def collect_agents(repo_root: Path, divisions: dict) -> tuple[list[dict], list[str]]:
    agents: list[dict] = []
    errors: list[str] = []
    for path in agent_files(repo_root, divisions):
        rel = path.relative_to(repo_root).as_posix()
        # Universal-newline read: a CRLF checkout parses the same as LF. (The
        # linter rejects CRLF separately; that is not this script's job.)
        text = path.read_text(encoding="utf-8")
        fields = parse_frontmatter(text)
        if fields is None:
            errors.append(f"{rel}: no frontmatter (first line must be '---', closed by a second '---')")
            continue
        missing = [f for f in REQUIRED_FIELDS if not fields.get(f, "").strip()]
        if missing:
            errors.append(f"{rel}: missing required frontmatter field(s): {', '.join(missing)}")
            continue
        entry = {
            "slug": path.stem,
            "install_slug": slugify(fields["name"]),
            "path": rel,
            "division": rel.split("/", 1)[0],
            "name": fields["name"].strip(),
            "description": fields["description"].strip(),
            "emoji": fields["emoji"].strip(),
            "color": fields["color"].strip(),
        }
        for field in OPTIONAL_FIELDS:
            entry[field] = fields.get(field, "").strip()
        if not entry["install_slug"]:
            errors.append(f"{rel}: name {entry['name']!r} has no ASCII letters or digits, so it has no install slug")
            continue
        agents.append(entry)

    for key, label in (("slug", "filename slug"), ("install_slug", "install slug (slugified name)")):
        seen: dict[str, str] = {}
        for agent in agents:
            if agent[key] in seen:
                errors.append(
                    f"duplicate {label} {agent[key]!r}: {seen[agent[key]]} and {agent['path']}"
                )
            else:
                seen[agent[key]] = agent["path"]

    agents.sort(key=lambda a: (a["division"], a["name"].lower(), a["slug"]))
    return agents, errors


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def normalize_repo_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise CatalogError(f"--repo-url must be an absolute http(s) URL, got {url!r}")
    if any(c in url for c in "\"'<>` \t\r\n\\"):
        raise CatalogError(f"--repo-url contains characters that are not allowed: {url!r}")
    return url if url.endswith("/") else url + "/"


def git_sha(repo_root: Path) -> str:
    env_sha = os.environ.get("GITHUB_SHA", "").strip()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, timeout=10
        )
        sha = out.stdout.strip()
        if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha):
            return sha
    except (OSError, subprocess.SubprocessError):
        pass
    return env_sha if re.fullmatch(r"[0-9a-f]{40}", env_sha) else ""


def build_date() -> str:
    # SOURCE_DATE_EPOCH keeps rebuilds reproducible when a caller wants that.
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    now = (
        _dt.datetime.fromtimestamp(int(epoch), _dt.timezone.utc)
        if epoch.isdigit()
        else _dt.datetime.now(_dt.timezone.utc)
    )
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def script_safe_json(value: object) -> str:
    """JSON that cannot end or confuse the <script> element it is inlined into.

    Escaping < > & covers `</script>`, `<!--` and `<script` sequences; U+2028
    and U+2029 are escaped for older JS parsers. JSON.parse reads all of these
    back unchanged.
    """
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    for raw, escaped in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                         ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        text = text.replace(raw, escaped)
    return text


def _csp_hash(body: str) -> str:
    digest = hashlib.sha256(body.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(digest).decode("ascii") + "'"


def render_html(template: str, catalog: dict) -> str:
    for placeholder in (DATA_PLACEHOLDER, CSP_PLACEHOLDER):
        if template.count(placeholder) != 1:
            raise CatalogError(f"{TEMPLATE_REL.as_posix()} must contain {placeholder} exactly once")

    # Content-Security-Policy: allow only the page's own inline <style> and
    # executable <script> blocks, by hash. The JSON data block is not
    # executable (type="application/json"), so it needs no allowance. Both are
    # resolved on the template, before any agent text is inlined, so agent
    # text can neither influence the hashes nor be mistaken for a placeholder.
    styles = re.findall(r"<style>(.*?)</style>", template, flags=re.S)
    scripts = re.findall(r"<script>(.*?)</script>", template, flags=re.S)
    if len(styles) != 1 or len(scripts) != 1:
        raise CatalogError(
            f"{TEMPLATE_REL.as_posix()} must have exactly one bare <style> and one bare <script> block "
            f"(found {len(styles)} and {len(scripts)})"
        )
    csp = (
        "default-src 'none'; "
        f"style-src {_csp_hash(styles[0])}; "
        f"script-src {_csp_hash(scripts[0])}; "
        "img-src data:; base-uri 'none'; form-action 'none'"
    )
    html = template.replace(CSP_PLACEHOLDER, csp)
    return html.replace(DATA_PLACEHOLDER, script_safe_json(catalog))


def build_catalog(repo_root: Path, repo_url: str) -> tuple[dict, list[str]]:
    divisions = load_divisions(repo_root)
    agents, errors = collect_agents(repo_root, divisions)
    catalog = {
        "meta": {
            "count": len(agents),
            "commit": git_sha(repo_root),
            "built": build_date(),
            "repo_url": repo_url,
        },
        "divisions": [
            {"id": key, "label": meta["label"], "icon": meta["icon"], "color": meta["color"]}
            for key, meta in divisions.items()
        ],
        "agents": agents,
    }
    return catalog, errors


def main(argv: list[str] | None = None) -> int:
    # Error lines can quote agent names; a legacy Windows console codepage
    # (cp1252) must not turn one into a UnicodeEncodeError traceback.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(
        description="Build the static agent catalog (agents.json + index.html).",
    )
    parser.add_argument("--out", type=Path, default=None,
                        help="output directory (default: _site/ at the repo root)")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL,
                        help="base URL that agent paths are appended to for 'View source' "
                             f"(default: {DEFAULT_REPO_URL})")
    parser.add_argument("--check", action="store_true",
                        help="parse and validate everything, render in memory, write nothing")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    try:
        repo_url = normalize_repo_url(args.repo_url)
        catalog, errors = build_catalog(repo_root, repo_url)
        if errors:
            for line in errors:
                print(f"ERROR {line}", file=sys.stderr)
            print(f"FAILED: {len(errors)} catalog error(s); nothing was written.", file=sys.stderr)
            return 1
        template = (repo_root / TEMPLATE_REL).read_text(encoding="utf-8")
        html = render_html(template, catalog)
    except (CatalogError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        print("FAILED: nothing was written.", file=sys.stderr)
        return 1

    count = catalog["meta"]["count"]
    ndiv = len(catalog["divisions"])
    if args.check:
        print(f"PASSED: {count} agents across {ndiv} divisions parse cleanly (--check: nothing written).")
        return 0

    out_dir = (args.out or (repo_root / "_site")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "agents.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8", newline="\n")
    commit = catalog["meta"]["commit"][:12] or "unknown commit"
    print(f"Built {count} agents across {ndiv} divisions ({commit}) -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
