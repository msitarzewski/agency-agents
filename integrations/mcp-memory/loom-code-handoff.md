# Source-checked handoff with Loom

The Backend Architect saves a response-shape decision. The Frontend Developer reads it, checks the referenced source, and decides whether the frontend can still rely on it. The Reality Checker checks that evidence before accepting the handoff.

This is a manual variant of the [RetroBoard memory workflow](../../examples/workflow-with-memory.md), using [ClickHouse Loom](https://github.com/ClickHouse/loom). It uses native tool names rather than the generic four-tool contract. Memory history does not roll back application files, database schemas, or deployments.

## Before the handoff

Use an already configured Loom MCP connection, following the project's installation instructions. Confirm that the connected server lists `loom_memory_set` and `loom_memory_get`. The request fields and read-result fields below are defined in the [Loom 1.3.0 memory models](https://github.com/ClickHouse/loom/blob/v1.3.0/server/memory/api/models_crud.py).

The roles here use the same configured project identity in an authorized namespace. They are prompt roles, not separate security principals. A deployment with independent identities must authorize each one; this example does not test that arrangement. Share no credentials in a memory or handoff. Project and receiver tags organize records; they grant no access.

## 1. Save a narrow decision and its evidence

For a small local RetroBoard fixture, put this helper in `src/task_view.py`:

```python
def task_view(task):
    return {"id": task["id"], "status": task["status"]}
```

It models a response body, not a running HTTP endpoint. Commit it in your own example repository. Record the full commit from `git rev-parse HEAD`, the repository you may share, and the exact path. Inspect the committed bytes with `git show <commit>:src/task_view.py`.

Ask the Backend Architect to call `loom_memory_set` with these arguments, replacing the namespace, repository, and commit placeholders:

```json
{
  "namespace": "<authorized-project-namespace>",
  "memory_key": "retroboard/handoffs/task-view",
  "value": {
    "decision": "The frontend reads id and status from task_view's response.",
    "repository": "<authorized-repository>",
    "commit": "<full-commit-id>",
    "path": "src/task_view.py",
    "symbol": "task_view",
    "assertion": "For a task containing id and status, task_view returns those fields unchanged.",
    "next": "Check the saved and current source before using this response shape."
  },
  "tags": ["project:retroboard", "receiver:frontend"]
}
```

Inspect the actual write response. A refusal, conflict, or no-op is not proof that this new decision was stored. Read back the exact key and compare the returned value with the intended handoff before telling the receiver it is available. Do not overwrite a conflicting decision to force this example through.

The repository, commit, path, and symbol above are writer-supplied evidence pointers. They are not attestation or an automatically tracked code link. This example does not set a `files` association or claim that such an association verifies source freshness.

## 2. Retrieve, then verify the source

Ask the Frontend Developer to call `loom_memory_get` with:

```json
{
  "namespace": "<authorized-project-namespace>",
  "memory_key": "retroboard/handoffs/task-view"
}
```

Continue only when `found` is true and `value` contains the intended handoff. Missing, refused, or unexpected results stop this handoff; do not guess another namespace or identity. No illustrative server response is supplied here.

Check out neither revision automatically. Read the saved source with `git show <saved-commit>:<saved-path>` and inspect the corresponding current source in the same authorized repository. Record both revisions and the current path. `git diff <saved-commit>..<current-commit> -- <saved-path>` can locate changes, but a clean path diff does not prove that callers, dependencies, or the whole API remain compatible.

For the fixture, evaluate `task_view({"id": "task-1", "status": "open"})` in the project's normal local check. The relevant result is `{"id": "task-1", "status": "open"}`. Verify the assertion rather than treating a changed hash as a verdict.

### A changed source can still support the decision

This replacement changes the source while preserving the fixture's response fields:

```python
def task_view(task):
    result = {"status": task["status"]}
    result["id"] = task["id"]
    return result
```

After checking it, the receiver may keep the decision and record the checked revision. This one input establishes only the fixture case, not general API compatibility.

This replacement invalidates the saved `status` assertion:

```python
def task_view(task):
    return {"id": task["id"], "state": task["status"]}
```

The receiver must reject that assertion for the new revision and coordinate the frontend/API change. A memory does not override the inspected code.

| Source observation                                              | Receiver action                                                                                                                  |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Saved and current helper match; the fixture assertion holds     | Use the checked decision for this fixture and record the revision.                                                               |
| Source changes but the refactor above preserves the assertion   | Keep the decision only after checking; record the new evidence.                                                                  |
| Current helper returns `state` instead of `status`              | Reject the outdated assertion and coordinate the contract change.                                                                |
| The path or symbol moved and its replacement is not established | Mark the handoff unresolved; find the authorized source before reuse.                                                            |
| The source cannot be read with the receiver's access            | Stop verification and ask the responsible project owner for permitted evidence; do not infer that the source is absent or wrong. |

## 3. Hand the result to the Reality Checker

Report the memory key, saved revision, inspected revision/path, exact assertion checked, result, and anything unresolved. The Reality Checker repeats the source check within its own authorized access; project-wide tags do not imply project-wide visibility. Keep any file, Git, schema, or deployment recovery separate from memory lookup and subject to the project's normal authorization.

These steps are a documented manual procedure. Static request checks and the local fixture do not establish live MCP transport, persistence, authorization enforcement, or automatic execution by an agent. Those need their own real-client validation before being claimed.
