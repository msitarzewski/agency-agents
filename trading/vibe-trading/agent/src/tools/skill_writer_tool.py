"""Skill management tools: full CRUD + auxiliary file support.

User-created skills are stored separately from bundled skills:
    ~/.vibe-trading/skills/user/<skill-name>/
        SKILL.md            # Main skill document
        references/         # Reference materials
        templates/          # Code/config templates
        examples/           # Example usage
        assets/             # Static files
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from src.agent.skills import USER_SKILLS_DIR
from src.agent.tools import BaseTool

_ALLOWED_SUBDIRS = {"references", "templates", "examples", "assets"}


def _sanitize_skill_name(name: str) -> str:
    """Sanitize skill name to a safe directory slug."""
    return re.sub(r"[^a-z0-9-]", "-", name.lower().strip())[:60]


class SaveSkillTool(BaseTool):
    """Save a successful workflow as a reusable skill."""

    name = "save_skill"
    description = (
        "Save a successful workflow or strategy template as a reusable skill. "
        "The skill will be available in future sessions via load_skill."
    )
    is_readonly = False
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name (lowercase, a-z0-9 and hyphens, e.g. 'crypto-mean-reversion')",
            },
            "content": {
                "type": "string",
                "description": "Full SKILL.md content including frontmatter (---\\nname: ...\\n---) and body",
            },
            "category": {
                "type": "string",
                "description": "Skill category (e.g. strategy, analysis, flow). Default: user",
            },
        },
        "required": ["name", "content"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        """Create or overwrite a user skill.

        Args:
            **kwargs: Must include name and content.

        Returns:
            JSON result string.
        """
        name = kwargs.get("name", "")
        content = kwargs.get("content", "")
        category = kwargs.get("category", "user")

        if not name or not content:
            return json.dumps({"status": "error", "error": "name and content required"})

        slug = _sanitize_skill_name(name)
        skill_dir = USER_SKILLS_DIR / slug
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"

        # Ensure frontmatter exists
        if not content.strip().startswith("---"):
            content = (
                f"---\nname: {slug}\n"
                f"description: User-created skill\n"
                f"category: {category}\n---\n\n{content}"
            )

        skill_path.write_text(content, encoding="utf-8")
        return json.dumps({
            "status": "ok",
            "message": f"Skill '{slug}' saved. Available via load_skill(\"{slug}\") in future sessions.",
            "path": str(skill_path),
        })


class PatchSkillTool(BaseTool):
    """Patch an existing skill with find-and-replace."""

    name = "patch_skill"
    description = (
        "Fix or update an existing skill by replacing specific text. "
        "Useful when a skill has outdated API parameters or incorrect examples."
    )
    is_readonly = False
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name to patch",
            },
            "find": {
                "type": "string",
                "description": "Text to find (exact match)",
            },
            "replace": {
                "type": "string",
                "description": "Replacement text",
            },
        },
        "required": ["name", "find", "replace"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        """Apply a find-and-replace patch to a skill.

        Searches user skills first, then bundled skills (copies to user dir before patching).

        Args:
            **kwargs: Must include name, find, replace.

        Returns:
            JSON result string.
        """
        name = kwargs.get("name", "")
        find_text = kwargs.get("find", "")
        replace_text = kwargs.get("replace", "")

        if not name or not find_text:
            return json.dumps({"status": "error", "error": "name and find required"})

        slug = _sanitize_skill_name(name)
        user_path = USER_SKILLS_DIR / slug / "SKILL.md"
        bundled_dir = Path(__file__).resolve().parents[1] / "skills"
        bundled_path = bundled_dir / slug / "SKILL.md"

        if user_path.exists():
            skill_path = user_path
        elif bundled_path.exists():
            # Copy bundled skill to user dir before patching
            user_path.parent.mkdir(parents=True, exist_ok=True)
            user_path.write_text(bundled_path.read_text(encoding="utf-8"), encoding="utf-8")
            skill_path = user_path
        else:
            return json.dumps({"status": "error", "error": f"Skill '{name}' not found"})

        content = skill_path.read_text(encoding="utf-8")
        if find_text not in content:
            return json.dumps({"status": "error", "error": f"Text not found in skill '{name}'"})

        patched = content.replace(find_text, replace_text, 1)
        skill_path.write_text(patched, encoding="utf-8")
        return json.dumps({
            "status": "ok",
            "message": f"Patched skill '{name}': replaced 1 occurrence.",
            "path": str(skill_path),
        })


class DeleteSkillTool(BaseTool):
    """Delete a user-created skill entirely."""

    name = "delete_skill"
    description = (
        "Delete a user-created skill and all its files. "
        "Only works on skills in ~/.vibe-trading/skills/user/. "
        "Cannot delete bundled skills."
    )
    is_readonly = False
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name to delete",
            },
        },
        "required": ["name"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Delete a user skill directory.

        Args:
            **kwargs: Must include name.

        Returns:
            JSON result string.
        """
        name = kwargs.get("name", "").strip()
        if not name:
            return json.dumps({"status": "error", "error": "name required"})

        slug = _sanitize_skill_name(name)
        skill_dir = USER_SKILLS_DIR / slug
        if not skill_dir.exists():
            return json.dumps({"status": "error", "error": f"User skill '{slug}' not found"})

        shutil.rmtree(skill_dir)
        return json.dumps({
            "status": "ok",
            "message": f"Deleted skill '{name}' and all its files.",
        })


class SkillFileTool(BaseTool):
    """Manage auxiliary files in a skill directory (references, templates, examples, assets)."""

    name = "skill_file"
    description = (
        "Manage auxiliary files in a skill directory. "
        "Actions: write (create/overwrite a file), remove (delete a file), list (show all files). "
        "Supported subdirs: references, templates, examples, assets."
    )
    is_readonly = False
    repeatable = True
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["write", "remove", "list"],
                "description": "Action to perform",
            },
            "skill_name": {
                "type": "string",
                "description": "Skill name (must exist in user skills)",
            },
            "path": {
                "type": "string",
                "description": "File path relative to skill dir (e.g. 'templates/sma_crossover.py'). Required for write/remove.",
            },
            "content": {
                "type": "string",
                "description": "File content. Required for write action.",
            },
        },
        "required": ["action", "skill_name"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Manage skill auxiliary files.

        Args:
            **kwargs: action, skill_name, and optionally path/content.

        Returns:
            JSON result string.
        """
        action = kwargs.get("action", "")
        skill_name = kwargs.get("skill_name", "").strip()

        if not skill_name:
            return json.dumps({"status": "error", "error": "skill_name required"})

        skill_dir = USER_SKILLS_DIR / _sanitize_skill_name(skill_name)
        if not skill_dir.exists():
            return json.dumps({"status": "error", "error": f"User skill '{skill_name}' not found. Create it with save_skill first."})

        if action == "list":
            return self._list_files(skill_dir, skill_name)
        elif action == "write":
            return self._write_file(skill_dir, skill_name, kwargs)
        elif action == "remove":
            return self._remove_file(skill_dir, skill_name, kwargs)
        else:
            return json.dumps({"status": "error", "error": f"Unknown action '{action}'. Use write, remove, or list."})

    @staticmethod
    def _list_files(skill_dir: Path, skill_name: str) -> str:
        """List all files in a skill directory."""
        files = []
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(skill_dir)
                files.append({"path": str(rel), "size": path.stat().st_size})
        return json.dumps({
            "status": "ok",
            "skill": skill_name,
            "files": files,
        }, ensure_ascii=False)

    @staticmethod
    def _write_file(skill_dir: Path, skill_name: str, kwargs: dict) -> str:
        """Write a file to a skill subdirectory."""
        rel_path = kwargs.get("path", "").strip()
        content = kwargs.get("content", "")
        if not rel_path:
            return json.dumps({"status": "error", "error": "path required for write"})
        if not content:
            return json.dumps({"status": "error", "error": "content required for write"})

        # Validate subdirectory
        parts = Path(rel_path).parts
        if len(parts) < 2 or parts[0] not in _ALLOWED_SUBDIRS:
            return json.dumps({
                "status": "error",
                "error": f"Path must start with one of: {', '.join(sorted(_ALLOWED_SUBDIRS))}. Got: '{parts[0] if parts else ''}'",
            })

        target = skill_dir / rel_path
        # Safety: prevent path traversal
        try:
            target.resolve().relative_to(skill_dir.resolve())
        except ValueError:
            return json.dumps({"status": "error", "error": "Path escapes skill directory"})

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return json.dumps({
            "status": "ok",
            "message": f"Written {rel_path} to skill '{skill_name}'.",
            "path": str(target),
        })

    @staticmethod
    def _remove_file(skill_dir: Path, skill_name: str, kwargs: dict) -> str:
        """Remove a file from a skill directory."""
        rel_path = kwargs.get("path", "").strip()
        if not rel_path:
            return json.dumps({"status": "error", "error": "path required for remove"})

        # Prevent deleting SKILL.md (use delete_skill for that)
        if Path(rel_path).name == "SKILL.md":
            return json.dumps({"status": "error", "error": "Cannot remove SKILL.md. Use delete_skill to remove the entire skill."})

        target = skill_dir / rel_path
        try:
            target.resolve().relative_to(skill_dir.resolve())
        except ValueError:
            return json.dumps({"status": "error", "error": "Path escapes skill directory"})

        if not target.exists():
            return json.dumps({"status": "error", "error": f"File not found: {rel_path}"})

        target.unlink()
        return json.dumps({
            "status": "ok",
            "message": f"Removed {rel_path} from skill '{skill_name}'.",
        })
