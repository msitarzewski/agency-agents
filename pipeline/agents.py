"""
Agent registry – loads every DreamEngine agent spec from disk
and exposes them by name, division, and phase.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AgentSpec:
    """Parsed representation of a single DreamEngine agent."""
    name: str
    description: str
    emoji: str
    vibe: str
    division: str          # directory name (engineering, design, …)
    file_path: str
    system_prompt: str     # full markdown body (used as LLM system prompt)


# ---------------------------------------------------------------------------
# Phase → agent mapping  (mirrors NEXUS playbooks)
# ---------------------------------------------------------------------------

PHASE_AGENTS: dict[str, list[str]] = {
    "discover": [
        "Trend Researcher",
        "Feedback Synthesizer",
        "UX Researcher",
        "Analytics Reporter",
        "Legal Compliance Checker",
        "Tool Evaluator",
    ],
    "strategize": [
        "Studio Producer",
        "Senior Project Manager",
        "Sprint Prioritizer",
        "UX Architect",
        "Brand Guardian",
        "Backend Architect",
        "Software Architect",
        "AI Engineer",
        "Finance Tracker",
    ],
    "scaffold": [
        "DevOps Automator",
        "Frontend Developer",
        "Backend Architect",
        "UX Architect",
        "Infrastructure Maintainer",
        "Studio Operations",
    ],
    "build": [
        "Agents Orchestrator",
        "Frontend Developer",
        "Backend Architect",
        "Senior Developer",
        "Mobile App Builder",
        "AI Engineer",
        "DevOps Automator",
        "Rapid Prototyper",
        "Code Reviewer",
        "Database Optimizer",
        "API Tester",
        "Evidence Collector",
        "Test Results Analyzer",
        "Performance Benchmarker",
    ],
    "harden": [
        "Reality Checker",
        "Evidence Collector",
        "Performance Benchmarker",
        "Security Engineer",
        "API Tester",
        "Accessibility Auditor",
        "Technical Writer",
        "Threat Detection Engineer",
    ],
    "launch": [
        "Studio Producer",
        "Analytics Reporter",
        "Content Creator",
        "Social Media Strategist",
        "Growth Hacker",
        "SEO Specialist",
        "App Store Optimizer",
        "DevOps Automator",
        "Infrastructure Maintainer",
        "Support Responder",
        "Project Shepherd",
        "Performance Benchmarker",
        "Experiment Tracker",
    ],
    "operate": [
        "Infrastructure Maintainer",
        "Support Responder",
        "DevOps Automator",
        "Analytics Reporter",
        "Feedback Synthesizer",
        "Sprint Prioritizer",
        "Growth Hacker",
        "Project Shepherd",
        "Experiment Tracker",
        "Content Creator",
        "Executive Summary Generator",
        "Finance Tracker",
        "Legal Compliance Checker",
        "Incident Response Commander",
        "SRE",
    ],
}


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML-ish frontmatter from a markdown file."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta


def _parse_body(text: str) -> str:
    """Return the markdown body after frontmatter."""
    m = re.match(r"^---\s*\n.*?\n---\s*\n?", text, re.DOTALL)
    return text[m.end():] if m else text


def load_all_agents(repo_root: str) -> dict[str, AgentSpec]:
    """
    Walk every division directory and load agent specs.
    Returns dict keyed by agent *name* (from frontmatter).
    """
    registry: dict[str, AgentSpec] = {}
    root = Path(repo_root)

    # Divisions are the top-level directories that contain agent .md files
    divisions = [
        "engineering", "design", "marketing", "product",
        "project-management", "testing", "support", "sales",
        "paid-media", "specialized", "spatial-computing",
        "game-development",
    ]

    for div in divisions:
        div_path = root / div
        if not div_path.is_dir():
            continue
        for md_file in sorted(div_path.glob("*.md")):
            try:
                raw = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            meta = _parse_frontmatter(raw)
            name = meta.get("name", md_file.stem.replace("-", " ").title())
            if not name:
                continue
            registry[name] = AgentSpec(
                name=name,
                description=meta.get("description", ""),
                emoji=meta.get("emoji", ""),
                vibe=meta.get("vibe", ""),
                division=div,
                file_path=str(md_file),
                system_prompt=_parse_body(raw),
            )

    return registry


def agents_for_phase(phase: str, registry: dict[str, AgentSpec]) -> list[AgentSpec]:
    """Return the AgentSpec objects assigned to a NEXUS phase."""
    names = PHASE_AGENTS.get(phase, [])
    return [registry[n] for n in names if n in registry]


def list_phases() -> list[str]:
    return list(PHASE_AGENTS.keys())
