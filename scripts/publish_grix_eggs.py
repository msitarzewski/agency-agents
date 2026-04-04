#!/usr/bin/env python3
"""Package agency agents into egg artifacts and publish them to Grix."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
import uuid
import zipfile
from dataclasses import dataclass
from html import unescape
from http import cookiejar
from pathlib import Path
from typing import Iterable
from urllib import error, parse, request


EXCLUDED_PERSONA_FILENAMES = {
    "ACCEPTANCE_REPORT.md",
    "SOURCE_INDEX.md",
    "TRACEABILITY.md",
}
SKIP_ARCHIVE_FILENAMES = {".DS_Store"}
REQUIRED_PERSONA_MARKERS = {"AGENTS.md", "IDENTITY.md", "SOUL.md"}


@dataclass(frozen=True)
class AgentPackage:
    egg_id: str
    source_markdown: Path
    source_dir: Path
    name: str
    description: str
    emoji: str
    color: str
    vibe: str


@dataclass(frozen=True)
class PublishArtifacts:
    skill_zip: Path
    openclaw_zip: Path


@dataclass(frozen=True)
class PublishResult:
    egg_id: str
    source_markdown: str
    source_dir: str
    created: bool
    version: int
    status: str
    persona_zip_url: str
    skill_zip_url: str


def fit_text(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1].rstrip() + "…"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create skill.zip/openclaw.zip pairs and publish eggs to Grix."
    )
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root to scan.",
    )
    parser.add_argument(
        "--base-url",
        default="https://grix.dhf.pub",
        help="Grix base URL.",
    )
    parser.add_argument("--username", required=True, help="Admin username.")
    parser.add_argument("--password", required=True, help="Admin password.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only publish the first N matched eggs. 0 means all.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N matched eggs before publishing.",
    )
    parser.add_argument(
        "--match",
        default="",
        help="Only publish eggs whose id/path contains this string.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Keep built artifacts in this directory instead of a temp dir.",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        default=None,
        help="Write JSON results to this file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build artifacts and print the publish plan without calling Grix.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra packaging details.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    packages = select_packages(
        discover_agent_packages(repo_root),
        match=args.match,
        offset=args.offset,
        limit=args.limit,
    )
    if not packages:
        print("No matching agent packages found.", file=sys.stderr)
        return 1

    artifact_dir, cleanup = prepare_artifact_dir(args.artifact_dir)
    try:
        artifacts_by_egg: dict[str, PublishArtifacts] = {}
        for package in packages:
            artifacts = build_publish_artifacts(package, artifact_dir)
            artifacts_by_egg[package.egg_id] = artifacts
            if args.verbose:
                summarize_artifacts(package, artifacts)

        if args.dry_run:
            print_plan(packages, artifact_dir, dry_run=True)
            write_report(args.report_file, [])
            return 0

        client = GrixAdminClient(
            base_url=args.base_url,
            username=args.username,
            password=args.password,
        )
        client.login()
        print_plan(packages, artifact_dir, dry_run=False)

        results: list[PublishResult] = []
        for index, package in enumerate(packages, start=1):
            artifacts = artifacts_by_egg[package.egg_id]
            result = client.publish(package, artifacts)
            results.append(result)
            print(
                f"[{index}/{len(packages)}] {result.egg_id} -> "
                f"version {result.version}, status={result.status}, created={result.created}"
            )

        write_report(args.report_file, results)
        return 0
    finally:
        cleanup()


def print_plan(packages: list[AgentPackage], artifact_dir: Path, dry_run: bool) -> None:
    mode = "dry-run" if dry_run else "publish"
    print(f"Mode: {mode}")
    print(f"Artifact directory: {artifact_dir}")
    print(f"Matched packages: {len(packages)}")
    for package in packages:
        print(f"  - {package.egg_id} ({package.source_markdown.relative_to(package.source_markdown.parents[1])})")


def prepare_artifact_dir(artifact_dir: Path | None) -> tuple[Path, callable]:
    if artifact_dir is not None:
        target = artifact_dir.resolve()
        target.mkdir(parents=True, exist_ok=True)
        return target, lambda: None

    tmp_dir = Path(tempfile.mkdtemp(prefix="grix-egg-artifacts-"))
    return tmp_dir, lambda: shutil.rmtree(tmp_dir, ignore_errors=True)


def discover_agent_packages(repo_root: Path) -> list[AgentPackage]:
    packages: list[AgentPackage] = []
    for markdown_file in sorted(repo_root.glob("*/*.md")):
        if markdown_file.name in {"README.md", "AGENTS.md", "SKILL.md"}:
            continue
        if markdown_file.parent.name == "scripts":
            continue
        sibling_dir = markdown_file.with_suffix("")
        if not sibling_dir.is_dir():
            continue
        if not REQUIRED_PERSONA_MARKERS.issubset({path.name for path in sibling_dir.iterdir() if path.is_file()}):
            continue
        frontmatter = parse_frontmatter(markdown_file)
        packages.append(
            AgentPackage(
                egg_id=markdown_file.stem,
                source_markdown=markdown_file,
                source_dir=sibling_dir,
                name=frontmatter.get("name", markdown_file.stem),
                description=frontmatter.get("description", ""),
                emoji=frontmatter.get("emoji", "🌍"),
                color=frontmatter.get("color", "#D97706"),
                vibe=frontmatter.get("vibe", ""),
            )
        )
    return packages


def select_packages(
    packages: list[AgentPackage], match: str, offset: int, limit: int
) -> list[AgentPackage]:
    filtered = packages
    needle = match.strip().lower()
    if needle:
        filtered = [
            package
            for package in filtered
            if needle in package.egg_id.lower()
            or needle in package.source_markdown.as_posix().lower()
        ]
    if offset > 0:
        filtered = filtered[offset:]
    if limit > 0:
        filtered = filtered[:limit]
    return filtered


def parse_frontmatter(markdown_file: Path) -> dict[str, str]:
    text = markdown_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}
    header = parts[0].splitlines()[1:]
    data: dict[str, str] = {}
    for line in header:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'").strip('"')
    return data


def build_publish_artifacts(package: AgentPackage, artifact_root: Path) -> PublishArtifacts:
    egg_dir = artifact_root / package.egg_id
    egg_dir.mkdir(parents=True, exist_ok=True)

    skill_zip = egg_dir / "skill.zip"
    with zipfile.ZipFile(skill_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("skill.md", package.source_markdown.read_text(encoding="utf-8"))

    openclaw_zip = egg_dir / "openclaw.zip"
    with zipfile.ZipFile(openclaw_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in iter_persona_files(package.source_dir):
            archive.write(file_path, arcname=file_path.relative_to(package.source_dir).as_posix())

    return PublishArtifacts(skill_zip=skill_zip, openclaw_zip=openclaw_zip)


def iter_persona_files(source_dir: Path) -> Iterable[Path]:
    for file_path in sorted(source_dir.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name in EXCLUDED_PERSONA_FILENAMES:
            continue
        if file_path.name in SKIP_ARCHIVE_FILENAMES:
            continue
        yield file_path


def summarize_artifacts(package: AgentPackage, artifacts: PublishArtifacts) -> None:
    skill_entries = list_zip_entries(artifacts.skill_zip)
    openclaw_entries = list_zip_entries(artifacts.openclaw_zip)
    print(f"Prepared {package.egg_id}")
    print(f"  skill.zip entries: {skill_entries}")
    print(f"  openclaw.zip entries: {len(openclaw_entries)} files")
    if any(Path(name).name in EXCLUDED_PERSONA_FILENAMES for name in openclaw_entries):
        raise RuntimeError(f"{package.egg_id} openclaw.zip unexpectedly contains excluded files")


def list_zip_entries(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path, "r") as archive:
        return sorted(archive.namelist())


class GrixAdminClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.cookie_jar = cookiejar.CookieJar()
        self.opener = request.build_opener(request.HTTPCookieProcessor(self.cookie_jar))
        self.session_token = ""

    def login(self) -> None:
        login_url = f"{self.base_url}/admin/login"
        page = self._read_text(request.Request(login_url, method="GET"))
        csrf_token = extract_csrf_token(page)
        payload = parse.urlencode(
            {
                "username": self.username,
                "password": self.password,
                "csrf_token": csrf_token,
            }
        ).encode("utf-8")
        req = request.Request(
            login_url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": login_url,
                "User-Agent": "agency-agents-grix-publisher/1.0",
            },
        )
        self._read_text(req)
        self.session_token = self._get_cookie("aibot_admin_session")
        if not self.session_token:
            raise RuntimeError("Admin login failed: session cookie not found.")

    def publish(self, package: AgentPackage, artifacts: PublishArtifacts) -> PublishResult:
        meta = {
            "id": package.egg_id,
            "color": normalize_color(package.color),
            "emoji": package.emoji or "🌍",
            "publish_now": True,
            "egg_i18n": [
                {
                    "locale": "zh-CN",
                    "name": fit_text(package.name, 128),
                    "description": package.description,
                    "vibe": fit_text(package.vibe, 128),
                },
                {
                    "locale": "en-US",
                    "name": fit_text(package.name, 128),
                    "description": package.description,
                    "vibe": fit_text(package.vibe, 128),
                },
            ],
            "version_i18n": [
                {"locale": "zh-CN", "version_desc": "Batch upload from agency-agents"},
                {"locale": "en-US", "version_desc": "Batch upload from agency-agents"},
            ],
            "artifact_manifest": {
                "source_repo": "agency-agents",
                "source_markdown": package.source_markdown.relative_to(package.source_markdown.parents[1]).as_posix(),
                "source_dir": package.source_dir.relative_to(package.source_dir.parents[1]).as_posix(),
                "excluded_persona_filenames": sorted(EXCLUDED_PERSONA_FILENAMES),
                "packaged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        }
        body, content_type = build_multipart_form(
            {
                "meta": (None, json.dumps(meta, ensure_ascii=False).encode("utf-8"), "application/json"),
                "openclaw_zip": (
                    "openclaw.zip",
                    artifacts.openclaw_zip.read_bytes(),
                    "application/zip",
                ),
                "skill_zip": (
                    "skill.zip",
                    artifacts.skill_zip.read_bytes(),
                    "application/zip",
                ),
            }
        )
        req = request.Request(
            f"{self.base_url}/v1/admin/eggs/create-with-files",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": content_type,
                "Accept": "application/json",
                "User-Agent": "agency-agents-grix-publisher/1.0",
            },
        )
        payload = self._read_json(req)
        if payload.get("code") != 0:
            raise RuntimeError(f"Publish failed for {package.egg_id}: {payload}")
        data = payload["data"]
        return PublishResult(
            egg_id=data["egg_id"],
            source_markdown=package.source_markdown.as_posix(),
            source_dir=package.source_dir.as_posix(),
            created=bool(data["created"]),
            version=int(data["version"]),
            status=str(data["status"]),
            persona_zip_url=str(data.get("persona_zip_url", "")),
            skill_zip_url=str(data.get("skill_zip_url", "")),
        )

    def _get_cookie(self, name: str) -> str:
        for item in self.cookie_jar:
            if item.name == name:
                return item.value
        return ""

    def _read_text(self, req: request.Request) -> str:
        try:
            with self.opener.open(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} for {req.full_url}: {body}") from exc

    def _read_json(self, req: request.Request) -> dict:
        text = self._read_text(req)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON response from {req.full_url}: {text}") from exc


def extract_csrf_token(page: str) -> str:
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', page)
    if not match:
        raise RuntimeError("Unable to find CSRF token on admin login page.")
    return unescape(match.group(1))


def normalize_color(raw: str) -> str:
    value = raw.strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return value.upper()
    mapped = {
        "cyan": "#00FFFF",
        "blue": "#3498DB",
        "green": "#2ECC71",
        "red": "#E74C3C",
        "purple": "#9B59B6",
        "orange": "#F39C12",
        "teal": "#008080",
        "indigo": "#6366F1",
        "pink": "#E84393",
        "gold": "#EAB308",
        "amber": "#F59E0B",
        "neon-green": "#10B981",
        "neon-cyan": "#06B6D4",
        "metallic-blue": "#3B82F6",
        "yellow": "#EAB308",
        "violet": "#8B5CF6",
        "rose": "#F43F5E",
        "lime": "#84CC16",
        "gray": "#6B7280",
        "fuchsia": "#D946EF",
    }
    return mapped.get(value.lower(), "#D97706")


def build_multipart_form(
    fields: dict[str, tuple[str | None, bytes, str | None]]
) -> tuple[bytes, str]:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    body = bytearray()
    for field_name, (filename, content, content_type) in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        disposition = f'Content-Disposition: form-data; name="{field_name}"'
        if filename:
            disposition += f'; filename="{filename}"'
        body.extend(f"{disposition}\r\n".encode("utf-8"))
        if content_type:
            body.extend(f"Content-Type: {content_type}\r\n".encode("utf-8"))
        body.extend(b"\r\n")
        body.extend(content)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def write_report(report_file: Path | None, results: list[PublishResult]) -> None:
    if report_file is None:
        return
    report_file = report_file.resolve()
    report_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "egg_id": result.egg_id,
            "source_markdown": result.source_markdown,
            "source_dir": result.source_dir,
            "created": result.created,
            "version": result.version,
            "status": result.status,
            "persona_zip_url": result.persona_zip_url,
            "skill_zip_url": result.skill_zip_url,
        }
        for result in results
    ]
    report_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
