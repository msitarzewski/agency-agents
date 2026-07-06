"""Security regressions for RememberTool persistent memory writes."""

from __future__ import annotations

import json
from pathlib import Path

from src.memory.persistent import PersistentMemory
from src.tools.remember_tool import RememberTool


def test_remember_rejects_memory_type_path_traversal(tmp_path: Path) -> None:
    """memory_type must not be able to escape the memory directory."""
    memory_dir = tmp_path / "memory"
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    tool = RememberTool(PersistentMemory(memory_dir=memory_dir))

    result = json.loads(tool.execute(
        action="save",
        title="Traversal Proof",
        content="SAFE_MARKER",
        memory_type="../outside/proof",
    ))

    assert result["status"] == "error"
    assert "memory_type" in result["error"]
    assert not (outside_dir / "proof_traversal_proof.md").exists()


def test_persistent_memory_rejects_unknown_memory_type(tmp_path: Path) -> None:
    """The storage layer enforces the documented memory type enum itself."""
    memory = PersistentMemory(memory_dir=tmp_path / "memory")

    try:
        memory.add("bad type", "content", "../../outside/proof")
    except ValueError as exc:
        assert "memory_type" in str(exc)
    else:  # pragma: no cover - makes the assertion message clearer on vulnerable code
        raise AssertionError("PersistentMemory.add() accepted an invalid memory_type")
