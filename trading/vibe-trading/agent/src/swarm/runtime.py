"""Swarm DAG orchestration runtime.

Core orchestrator: schedules workers by topological layer, parallel within each
layer and serial between layers. Execution runs in a background daemon thread
with cancellation and event callback support.
"""

from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
    TimeoutError as FuturesTimeoutError,
    as_completed,
)
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from src.config.schema import AgentConfig
from src.swarm import grounding
from src.swarm.models import (
    RunStatus,
    SwarmAgentSpec,
    SwarmEvent,
    SwarmRun,
    SwarmTask,
    TaskStatus,
    WorkerResult,
)
from src.swarm.presets import build_run_from_preset
from src.swarm.store import SwarmStore
from src.swarm.task_store import (
    TaskStore,
    resolve_dependencies,
    topological_layers,
    validate_dag,
)
from src.tools.redaction import redact_internal_paths
from src.swarm.worker import run_worker

logger = logging.getLogger(__name__)


class SwarmRuntime:
    """Swarm DAG orchestration engine.

    Manages the full lifecycle of a swarm run: creation, scheduling, execution,
    and cancellation. Each run executes in an independent background daemon thread;
    tasks within a layer run in parallel via ThreadPoolExecutor.

    Attributes:
        _store: SwarmStore persistence layer.
        _max_workers: Maximum concurrent workers in ThreadPoolExecutor.
    """

    def __init__(
        self,
        store: SwarmStore,
        max_workers: int = 4,
        agent_config: AgentConfig | None = None,
    ) -> None:
        """Initialize SwarmRuntime.

        Args:
            store: SwarmStore instance for run persistence.
            max_workers: Maximum concurrent worker threads.
            agent_config: Optional resolved agent config carrying remote MCP
                server definitions. Boot-time / operator-trusted; never derived
                from a swarm caller. Forwarded to every worker on every run so
                the worker can assemble a registry that includes remote MCP
                tools. ``None`` (the default) preserves the current
                local-tool-only behavior byte-for-byte.
        """
        self._store = store
        self._max_workers = max_workers
        self._agent_config = agent_config
        self._cancel_events: dict[str, threading.Event] = {}
        self._live_callbacks: dict[str, Callable] = {}
        self._lock = threading.Lock()

    def start_run(
        self,
        preset_name: str,
        user_vars: dict[str, str],
        live_callback: Callable | None = None,
        include_shell_tools: bool = False,
    ) -> SwarmRun:
        """Start a swarm run. Returns immediately, execution happens in background.

        Args:
            preset_name: YAML preset name to execute.
            user_vars: User-provided variables for prompt templates.
            live_callback: Optional callback invoked for each event in real-time.
            include_shell_tools: Whether workers may register shell tools.

        Returns:
            The created SwarmRun instance (status=pending initially).

        Raises:
            FileNotFoundError: If preset does not exist.
            ValueError: If DAG validation fails.
        """
        # Reap any previously running runs whose host process died without
        # finalizing them. Threshold is computed per-run from agent timeouts +
        # heartbeat interval (see SwarmStore.compute_stale_threshold), so a
        # legitimately slow long-running task is not killed.
        try:
            reaped = self._store.reap_stale_running_runs()
            if reaped:
                logger.info("Reaped %d stale swarm run(s): %s", len(reaped), reaped)
        except Exception:
            logger.warning("Stale-run reaper failed", exc_info=True)

        run = build_run_from_preset(preset_name, user_vars)
        validate_dag(run.tasks)

        # Capture which provider/model the run was launched against so the
        # serialized run.json carries enough context for cost audits and
        # post-hoc debugging. Read directly from the same env vars the
        # provider layer uses (src/providers/llm.py:136,195) — that way an
        # override applied via os.environ still shows up. Per-agent overrides
        # remain visible on SwarmAgentSpec.model_name.
        run.provider = (os.getenv("LANGCHAIN_PROVIDER") or "").strip().lower() or None
        run.model = (os.getenv("LANGCHAIN_MODEL_NAME") or "").strip() or None

        self._store.create_run(run)

        cancel_event = threading.Event()
        with self._lock:
            self._cancel_events[run.id] = cancel_event
            if live_callback is not None:
                self._live_callbacks[run.id] = live_callback

        thread = threading.Thread(
            target=self._execute_run,
            args=(run, cancel_event, include_shell_tools),
            name=f"swarm-{run.id}",
            daemon=True,
        )
        thread.start()

        return run

    def cancel_run(self, run_id: str) -> bool:
        """Signal cancellation for a running swarm.

        Args:
            run_id: ID of the run to cancel.

        Returns:
            True if cancellation was signalled, False if run not found.
        """
        with self._lock:
            cancel_event = self._cancel_events.get(run_id)
        if cancel_event is None:
            return False
        cancel_event.set()
        return True

    def _emit_event(self, run_id: str, event: SwarmEvent) -> None:
        """Persist an event and forward to live callback if registered.

        Args:
            run_id: Run identifier.
            event: Event to persist.
        """
        try:
            self._store.append_event(run_id, event)
        except Exception:
            logger.warning("Failed to persist event for run %s", run_id, exc_info=True)
        with self._lock:
            cb = self._live_callbacks.get(run_id)
        if cb is not None:
            try:
                cb(event)
            except Exception:
                logger.warning("Live callback failed for run %s", run_id, exc_info=True)

    def _make_event(
        self,
        event_type: str,
        agent_id: str | None = None,
        task_id: str | None = None,
        data: dict | None = None,
    ) -> SwarmEvent:
        """Create a SwarmEvent with current timestamp.

        Args:
            event_type: Event type string.
            agent_id: Optional agent identifier.
            task_id: Optional task identifier.
            data: Optional additional data.

        Returns:
            SwarmEvent instance.
        """
        return SwarmEvent(
            type=event_type,
            agent_id=agent_id,
            task_id=task_id,
            data=data or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _execute_run(
        self,
        run: SwarmRun,
        cancel_event: threading.Event,
        include_shell_tools: bool = False,
    ) -> None:
        """Core orchestration loop (runs in background thread).

        Steps:
            1. Update run status to running
            2. Initialize TaskStore, save all tasks
            3. Compute topological layers
            4. For each layer:
               a. Check cancellation
               b. Submit all tasks to ThreadPoolExecutor
               c. Collect results, resolve dependencies, update store
            5. Update run status to completed/failed

        Args:
            run: SwarmRun to execute.
            cancel_event: Threading event for cancellation signalling.
            include_shell_tools: Whether workers may register shell tools.
        """
        run_id = run.id
        run_dir = self._store.run_dir(run_id)

        # Mark as running
        run.status = RunStatus.running
        self._store.update_run(run)
        self._emit_event(run_id, self._make_event("run_started"))

        self._prefetch_grounding_data(run)

        # Initialize task store
        task_store = TaskStore(run_dir)
        for task in run.tasks:
            task_store.save_task(task)

        # Build agent lookup
        agent_map: dict[str, SwarmAgentSpec] = {a.id: a for a in run.agents}

        # Render the grounding block once and pass it to every worker on
        # this run. The block is empty when no symbols were detected, in
        # which case workers see no extra section.
        grounding_block = grounding.format_grounding_block(run.grounding_data or {})

        # Compute execution layers
        layers = topological_layers(run.tasks)
        task_summaries: dict[str, str] = {}
        all_succeeded = True

        try:
            for layer_idx, layer_task_ids in enumerate(layers):
                # Check cancellation between layers
                if cancel_event.is_set():
                    logger.info("Run %s cancelled at layer %d", run_id, layer_idx)
                    self._cancel_remaining_tasks(task_store, layer_task_ids, run.tasks)
                    all_succeeded = False
                    break

                self._emit_event(
                    run_id,
                    self._make_event(
                        "layer_started",
                        data={"layer": layer_idx, "tasks": layer_task_ids},
                    ),
                )

                # Execute all tasks in this layer in parallel
                layer_results = self._execute_layer(
                    run=run,
                    task_store=task_store,
                    agent_map=agent_map,
                    layer_task_ids=layer_task_ids,
                    task_summaries=task_summaries,
                    run_dir=run_dir,
                    cancel_event=cancel_event,
                    include_shell_tools=include_shell_tools,
                    grounding_block=grounding_block,
                )

                # Process results
                for tid, result in layer_results.items():
                    # Accumulate token counts to run totals
                    run.total_input_tokens += result.input_tokens
                    run.total_output_tokens += result.output_tokens

                    if result.status == "completed":
                        task_summaries[tid] = result.summary
                        now_iso = datetime.now(timezone.utc).isoformat()
                        task_store.update_status(
                            tid,
                            TaskStatus.completed,
                            summary=result.summary,
                            completed_at=now_iso,
                            artifacts=result.artifact_paths,
                            worker_iterations=result.iterations,
                        )
                        resolve_dependencies(run_dir / "tasks", tid)
                        self._emit_event(
                            run_id,
                            self._make_event(
                                "task_completed",
                                task_id=tid,
                                data={
                                    "status": result.status,
                                    "iterations": result.iterations,
                                    "input_tokens": result.input_tokens,
                                    "output_tokens": result.output_tokens,
                                },
                            ),
                        )
                    else:
                        all_succeeded = False
                        task_store.update_status(
                            tid,
                            TaskStatus.failed,
                            error=redact_internal_paths(result.error)
                            or f"worker did not complete (status={result.status})",
                            completed_at=datetime.now(timezone.utc).isoformat(),
                            worker_iterations=result.iterations,
                        )
                        self._emit_event(
                            run_id,
                            self._make_event(
                                "task_failed",
                                task_id=tid,
                                data={
                                    "error": redact_internal_paths(result.error),
                                    "input_tokens": result.input_tokens,
                                    "output_tokens": result.output_tokens,
                                },
                            ),
                        )

                # Tasks blocked by a failed upstream are never dispatched and
                # therefore not present in layer_results — they were already
                # marked TaskStatus.blocked in _execute_layer and emitted
                # task_blocked. Account for them in run-level status so the
                # run is marked failed, not silently completed.
                for tid in layer_task_ids:
                    if tid not in layer_results:
                        all_succeeded = False

                # Snapshot run.json at the layer boundary so list_runs and any
                # client that reads run.json directly sees fresh task statuses
                # without per-task I/O spam. One write per layer is cheap.
                self._sync_run_tasks_snapshot(run, task_store)

        except Exception as exc:
            logger.error("Run %s failed with exception", run_id, exc_info=True)
            all_succeeded = False
            self._emit_event(
                run_id,
                self._make_event("run_error", data={"error": redact_internal_paths(str(exc))}),
            )

        # Finalize run
        final_status = (
            RunStatus.cancelled if cancel_event.is_set() else RunStatus.completed if all_succeeded else RunStatus.failed
        )
        run.status = final_status
        run.completed_at = datetime.now(timezone.utc).isoformat()

        # Sync tasks back to run model
        run.tasks = task_store.load_all()

        # Set final report from aggregation task (last task) if available
        if task_summaries:
            last_layer = layers[-1] if layers else []
            for tid in last_layer:
                if tid in task_summaries:
                    run.final_report = task_summaries[tid]
                    break

        self._store.update_run(run)
        self._emit_event(run_id, self._make_event("run_completed", data={"status": final_status.value}))

        # Cleanup cancel event and live callback
        with self._lock:
            self._cancel_events.pop(run_id, None)
            self._live_callbacks.pop(run_id, None)

    def _sync_run_tasks_snapshot(self, run: SwarmRun, task_store: TaskStore) -> None:
        """Mirror live ``tasks/*.json`` back into ``run.json`` at a safe point.

        Called at layer boundaries only — not per-task — to keep run.json a
        useful coarse snapshot for ``list_runs`` and CLI/Web callers that
        don't hydrate per request. Failures are logged but never fatal: the
        per-task files are still the live source of truth.
        """
        try:
            run.tasks = task_store.load_all()
            self._store.update_run(run)
        except Exception:
            logger.warning("Layer-boundary run.json sync failed", exc_info=True)

    def _prefetch_grounding_data(self, run: SwarmRun) -> None:
        """Fetch run-level grounding data without blocking ``start_run``."""
        symbols = grounding.extract_symbols_from_user_vars(run.user_vars)
        if not symbols:
            return

        symbol_limit = grounding.max_grounding_symbols()
        if len(symbols) > symbol_limit:
            logger.warning(
                "grounding: limiting run %s symbols from %d to %d",
                run.id,
                len(symbols),
                symbol_limit,
            )
            symbols = symbols[:symbol_limit]

        # Multi-symbol grounding fetch can take 30s+ on slow loaders. Wrap it
        # in a heartbeat so events.jsonl gets fresh entries during the fetch
        # — without this, the stale-run reaper would false-positive-mark a
        # healthy fresh run that's just waiting on OHLCV API calls.
        from src.agent.progress import HeartbeatTimer

        def _on_grounding_heartbeat(payload: dict) -> None:
            self._emit_event(
                run.id,
                self._make_event(
                    "run_heartbeat",
                    data={**payload, "phase": "grounding"},
                ),
            )

        try:
            interval = float(os.getenv("SWARM_HEARTBEAT_INTERVAL_S", "3.0"))
        except ValueError:
            interval = 3.0

        try:
            with HeartbeatTimer(
                tool_name=f"grounding:{len(symbols)}symbols",
                interval=interval,
                emit=_on_grounding_heartbeat,
            ):
                fetched = grounding.fetch_grounding_data(symbols)
        except Exception:
            logger.warning(
                "grounding: pre-fetch failed for run %s symbols=%s",
                run.id,
                symbols,
                exc_info=True,
            )
            return

        if fetched:
            run.grounding_data = fetched
            self._store.update_run(run)

    def _execute_layer(
        self,
        run: SwarmRun,
        task_store: TaskStore,
        agent_map: dict[str, SwarmAgentSpec],
        layer_task_ids: list[str],
        task_summaries: dict[str, str],
        run_dir: Path,
        cancel_event: threading.Event,
        include_shell_tools: bool = False,
        grounding_block: str = "",
    ) -> dict[str, WorkerResult]:
        """Execute all tasks in a single layer in parallel, with retry on failure.

        Each task is retried up to agent_spec.max_retries times if the worker
        returns status="failed". A "task_retry" event is emitted before each retry.

        Args:
            run: The SwarmRun being executed.
            task_store: TaskStore for task persistence.
            agent_map: Agent specs keyed by agent_id.
            layer_task_ids: Task IDs in this layer.
            task_summaries: Accumulated task summaries from previous layers.
            run_dir: Run directory path.
            cancel_event: Cancellation event.
            include_shell_tools: Whether workers may register shell tools.
            grounding_block: Pre-rendered "Ground Truth" markdown for workers.

        Returns:
            Mapping of task_id -> WorkerResult for all tasks in this layer.
        """
        results: dict[str, WorkerResult] = {}

        def _event_callback(event: SwarmEvent) -> None:
            self._emit_event(run.id, event)

        # Manual executor lifecycle (not `with`) so KeyboardInterrupt and
        # the layer deadline don't block main on `shutdown(wait=True)` —
        # `wait=False + cancel_futures=True` lets pending work drop and
        # the CLI return immediately. Running workers finish naturally.
        executor = ThreadPoolExecutor(max_workers=self._max_workers)
        futures: dict[Future[WorkerResult], str] = {}
        layer_budget = 0  # seconds — max per-task (retries × timeout) across layer
        try:
            for tid in layer_task_ids:
                task = task_store.load_task(tid)

                # Dependency-aware gating: without this check, a failed upstream
                # silently produces an empty task_summaries entry (the worker
                # upstream loop below only copies summaries that exist) and the
                # downstream worker runs with no upstream context. For an
                # investment-committee preset where portfolio_manager
                # depends_on=["task-risk"], a failed risk_officer would let PM
                # produce a "decision" with no risk input — which is
                # safety-critical. Mark blocked and skip dispatch; same-layer
                # peers with no shared upstream are unaffected.
                blocked_upstreams: list[tuple[str, str]] = []
                for dep_id in task.depends_on:
                    try:
                        dep_task = task_store.load_task(dep_id)
                    except FileNotFoundError:
                        blocked_upstreams.append((dep_id, "missing"))
                        continue
                    if dep_task.status != TaskStatus.completed:
                        blocked_upstreams.append((dep_id, dep_task.status.value))

                if blocked_upstreams:
                    reason = ", ".join(f"{d}={s}" for d, s in blocked_upstreams)
                    blocked_by_ids = [d for d, _ in blocked_upstreams]
                    task_store.update_status(
                        tid,
                        TaskStatus.blocked,
                        error=f"Blocked: upstream not completed ({reason})",
                        blocked_by=blocked_by_ids,
                        completed_at=datetime.now(timezone.utc).isoformat(),
                    )
                    self._emit_event(
                        run.id,
                        self._make_event(
                            "task_blocked",
                            agent_id=task.agent_id,
                            task_id=tid,
                            data={"blocked_by": blocked_by_ids, "reason": reason},
                        ),
                    )
                    continue

                agent_spec = agent_map.get(task.agent_id)
                if agent_spec is None:
                    results[tid] = WorkerResult(
                        status="failed",
                        summary="",
                        error=f"Agent '{task.agent_id}' not found in preset",
                    )
                    continue

                # Mark task as in_progress
                task_store.update_status(
                    tid,
                    TaskStatus.in_progress,
                    started_at=datetime.now(timezone.utc).isoformat(),
                )
                self._emit_event(
                    run.id,
                    self._make_event("task_started", agent_id=agent_spec.id, task_id=tid),
                )

                # Build upstream summaries from input_from mapping
                upstream: dict[str, str] = {}
                for context_key, source_task_id in task.input_from.items():
                    if source_task_id in task_summaries:
                        upstream[context_key] = task_summaries[source_task_id]

                future = executor.submit(
                    self._run_worker_with_retries,
                    agent_spec=agent_spec,
                    task=task,
                    upstream_summaries=upstream,
                    user_vars=run.user_vars,
                    run_dir=run_dir,
                    event_callback=_event_callback,
                    run_id=run.id,
                    include_shell_tools=include_shell_tools,
                    grounding_block=grounding_block,
                )
                futures[future] = tid
                per_task_budget = agent_spec.timeout_seconds * (agent_spec.max_retries + 1)
                layer_budget = max(layer_budget, per_task_budget)

            # Collect results with a hard layer-level deadline — defends against
            # worker threads stuck in C extensions / blocked I/O that bypass the
            # in-loop timeout check (issue #42).
            deadline_buffer = 60
            layer_deadline = layer_budget + deadline_buffer if layer_budget else None

            try:
                for future in as_completed(futures, timeout=layer_deadline):
                    tid = futures[future]
                    try:
                        results[tid] = future.result()
                    except Exception as exc:
                        logger.error("Worker for task %s raised exception", tid, exc_info=True)
                        results[tid] = WorkerResult(
                            status="failed",
                            summary="",
                            error=str(exc),
                        )
            except FuturesTimeoutError:
                for pending, tid in futures.items():
                    if tid in results:
                        continue
                    pending.cancel()
                    logger.error(
                        "Worker for task %s exceeded layer deadline (%ds)",
                        tid,
                        layer_deadline,
                    )
                    results[tid] = WorkerResult(
                        status="timeout",
                        summary="",
                        error=f"Worker exceeded layer deadline of {layer_deadline}s",
                    )
        except KeyboardInterrupt:
            cancel_event.set()
            logger.warning("Swarm layer interrupted — cancelling pending workers")
            raise
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return results

    def _run_worker_with_retries(
        self,
        agent_spec: SwarmAgentSpec,
        task: SwarmTask,
        upstream_summaries: dict[str, str],
        user_vars: dict[str, str],
        run_dir: Path,
        event_callback: Callable[[SwarmEvent], None] | None,
        run_id: str,
        include_shell_tools: bool = False,
        grounding_block: str = "",
    ) -> WorkerResult:
        """Run a worker with automatic retry on failure.

        Retries up to agent_spec.max_retries times. Emits a "task_retry" event
        before each retry attempt. Token counts are accumulated across all
        attempts.

        Args:
            agent_spec: Agent role specification.
            task: The task to execute.
            upstream_summaries: Summaries from upstream tasks.
            user_vars: User-provided template variables.
            run_dir: Run directory path.
            event_callback: Optional event callback.
            run_id: Run identifier for event emission.
            include_shell_tools: Whether the worker may register shell tools.
            grounding_block: Pre-rendered "Ground Truth" markdown spliced
                into the worker's system prompt. Empty string when no
                symbols were extracted from user_vars.

        Returns:
            WorkerResult from the last attempt.
        """
        max_retries = agent_spec.max_retries
        cumulative_input_tokens = 0
        cumulative_output_tokens = 0
        result: WorkerResult | None = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                self._emit_event(
                    run_id,
                    self._make_event(
                        "task_retry",
                        agent_id=agent_spec.id,
                        task_id=task.id,
                        data={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "previous_error": result.error if result else None,
                        },
                    ),
                )
                logger.info(
                    "Retrying task %s (attempt %d/%d)",
                    task.id,
                    attempt + 1,
                    max_retries + 1,
                )

            result = run_worker(
                agent_spec=agent_spec,
                task=task,
                upstream_summaries=upstream_summaries,
                user_vars=user_vars,
                run_dir=run_dir,
                event_callback=event_callback,
                include_shell_tools=include_shell_tools,
                grounding_block=grounding_block,
                agent_config=self._agent_config,
            )

            cumulative_input_tokens += result.input_tokens
            cumulative_output_tokens += result.output_tokens

            if result.status != "failed":
                # Success (or timeout/token_limit/completed) — no more retries
                result = result.model_copy(
                    update={
                        "input_tokens": cumulative_input_tokens,
                        "output_tokens": cumulative_output_tokens,
                    }
                )
                return result

        # All retries exhausted, return the last failed result with cumulative tokens
        if result is not None:
            result = result.model_copy(
                update={
                    "input_tokens": cumulative_input_tokens,
                    "output_tokens": cumulative_output_tokens,
                }
            )
        return result  # type: ignore[return-value]

    def _cancel_remaining_tasks(
        self,
        task_store: TaskStore,
        current_layer_ids: list[str],
        all_tasks: list[SwarmTask],
    ) -> None:
        """Mark all non-completed tasks as cancelled.

        Args:
            task_store: TaskStore for persistence.
            current_layer_ids: Task IDs in the current (interrupted) layer.
            all_tasks: All tasks in the run.
        """
        for task in all_tasks:
            if task.status not in (TaskStatus.completed, TaskStatus.failed):
                try:
                    task_store.update_status(task.id, TaskStatus.cancelled)
                except Exception:
                    logger.warning("Failed to cancel task %s", task.id, exc_info=True)
