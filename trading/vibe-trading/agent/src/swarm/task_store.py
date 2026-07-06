"""Swarm multi-agent system — Task persistence and DAG algorithms.

Each task is stored independently as tasks/task-{id}.json with full CRUD support.
Provides DAG algorithms: dependency resolution, cycle detection, and topological layering.
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from pathlib import Path

from src.swarm.models import SwarmTask, TaskStatus


class TaskStore:
    """File-based persistence layer for tasks.

    Each task is stored at run_dir/tasks/task-{id}.json.

    Attributes:
        run_dir: Root directory of the current run.
    """

    def __init__(self, run_dir: Path) -> None:
        """Initialize TaskStore.

        Args:
            run_dir: Path to .swarm/runs/{run_id}/ directory.
        """
        self.run_dir = run_dir
        self._tasks_dir = run_dir / "tasks"
        self._tasks_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _task_path(self, task_id: str) -> Path:
        """Return the file path for a task.

        Args:
            task_id: Task ID.

        Returns:
            Path to the task JSON file.
        """
        return self._tasks_dir / f"task-{task_id}.json"

    def save_task(self, task: SwarmTask) -> None:
        """Save or overwrite task state.

        Args:
            task: SwarmTask instance.
        """
        path = self._task_path(task.id)
        tmp_path = path.with_suffix(".tmp")
        with self._lock:
            tmp_path.write_text(task.model_dump_json(indent=2), encoding="utf-8")
            tmp_path.replace(path)

    def load_task(self, task_id: str) -> SwarmTask:
        """Load a task by ID.

        Args:
            task_id: Task ID.

        Returns:
            SwarmTask instance.

        Raises:
            FileNotFoundError: If the task file does not exist.
        """
        path = self._task_path(task_id)
        if not path.exists():
            raise FileNotFoundError(f"Task not found: {path.name}")
        return SwarmTask.model_validate_json(path.read_text(encoding="utf-8"))

    def load_all(self) -> list[SwarmTask]:
        """Load all tasks for the current run.

        Returns:
            List of SwarmTask sorted by ID.
        """
        tasks: list[SwarmTask] = []
        for path in sorted(self._tasks_dir.glob("task-*.json")):
            tasks.append(
                SwarmTask.model_validate_json(path.read_text(encoding="utf-8"))
            )
        return tasks

    def update_status(
        self, task_id: str, status: TaskStatus, **kwargs: str | int | list[str] | None
    ) -> SwarmTask:
        """Update task status and additional fields.

        Args:
            task_id: Task ID.
            status: New status.
            **kwargs: Optional fields such as summary, error, completed_at, artifacts, etc.

        Returns:
            Updated SwarmTask instance.
        """
        task = self.load_task(task_id)
        updated_data = task.model_dump()
        updated_data["status"] = status
        for key, value in kwargs.items():
            if key in updated_data:
                updated_data[key] = value
        updated_task = SwarmTask.model_validate(updated_data)
        self.save_task(updated_task)
        return updated_task


def resolve_dependencies(tasks_dir: Path, completed_task_id: str) -> list[str]:
    """Remove a completed task ID from blocked_by in all downstream tasks.

    Scans all task files under tasks_dir and removes completed_task_id from each
    task's blocked_by list. If a task's blocked_by becomes empty and its status
    is blocked, it is marked as newly unblocked (pending).

    Args:
        tasks_dir: Path to the tasks/ directory.
        completed_task_id: ID of the just-completed task.

    Returns:
        List of newly unblocked task IDs (blocked_by went from non-empty to empty).
    """
    newly_unblocked: list[str] = []

    for path in tasks_dir.glob("task-*.json"):
        task = SwarmTask.model_validate_json(path.read_text(encoding="utf-8"))
        if completed_task_id not in task.blocked_by:
            continue

        new_blocked_by = [tid for tid in task.blocked_by if tid != completed_task_id]
        updated_data = task.model_dump()
        updated_data["blocked_by"] = new_blocked_by

        if not new_blocked_by and task.status == TaskStatus.blocked:
            updated_data["status"] = TaskStatus.pending
            newly_unblocked.append(task.id)

        updated_task = SwarmTask.model_validate(updated_data)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(updated_task.model_dump_json(indent=2), encoding="utf-8")
        tmp_path.replace(path)

    return newly_unblocked


def validate_dag(tasks: list[SwarmTask]) -> None:
    """DFS cycle detection to ensure the task DAG is acyclic.

    Args:
        tasks: List of SwarmTask.

    Raises:
        ValueError: If a cycle is detected; message includes the cycle path.
    """
    graph: dict[str, list[str]] = {t.id: list(t.depends_on) for t in tasks}
    all_ids = {t.id for t in tasks}

    for task in tasks:
        for dep in task.depends_on:
            if dep not in all_ids:
                raise ValueError(
                    f"Task '{task.id}' depends on unknown task '{dep}'"
                )

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {tid: WHITE for tid in all_ids}
    path: list[str] = []

    def dfs(node: str) -> None:
        """DFS traversal to detect back edges.

        Args:
            node: Current node ID.

        Raises:
            ValueError: If a cycle is detected.
        """
        color[node] = GRAY
        path.append(node)

        for neighbor in graph.get(node, []):
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                raise ValueError(
                    f"Cycle detected in task DAG: {' -> '.join(cycle)}"
                )
            if color[neighbor] == WHITE:
                dfs(neighbor)

        path.pop()
        color[node] = BLACK

    for tid in all_ids:
        if color[tid] == WHITE:
            dfs(tid)


def topological_layers(tasks: list[SwarmTask]) -> list[list[str]]:
    """Kahn's algorithm topological layering; tasks in the same layer can run in parallel.

    Args:
        tasks: List of SwarmTask (must be a valid acyclic DAG).

    Returns:
        List of layers in execution order; each layer contains task IDs that can
        run in parallel.

    Raises:
        ValueError: If the DAG contains a cycle (topological sort cannot complete).
    """
    in_degree: dict[str, int] = {t.id: 0 for t in tasks}
    dependents: dict[str, list[str]] = defaultdict(list)

    for task in tasks:
        in_degree[task.id] = len(task.depends_on)
        for dep in task.depends_on:
            dependents[dep].append(task.id)

    queue: deque[str] = deque(
        tid for tid, deg in in_degree.items() if deg == 0
    )

    layers: list[list[str]] = []
    processed = 0

    while queue:
        layer: list[str] = list(queue)
        queue.clear()
        layers.append(layer)
        processed += len(layer)

        for tid in layer:
            for downstream in dependents[tid]:
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    queue.append(downstream)

    if processed != len(tasks):
        raise ValueError(
            f"DAG contains a cycle: processed {processed}/{len(tasks)} tasks"
        )

    return layers
