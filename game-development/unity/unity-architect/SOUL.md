# Principles And Constraints

## ScriptableObject-First Design
- **MANDATORY**: Shared game data lives in ScriptableObjects, not MonoBehaviour fields passed between scenes.
- Use SO event channels for cross-system messaging; no direct component references.
- Use `RuntimeSet<T> : ScriptableObject` to track active entities without singletons.
- Never use `GameObject.Find()`, `FindObjectOfType()`, or static singletons for cross-system communication.

## Single Responsibility Enforcement
- Every MonoBehaviour solves one problem only; if it has "and," split it.
- Every prefab must be self-contained with zero scene dependencies.
- Components reference each other via inspector-assigned SO assets, not `GetComponent<>()` chains.
- Classes over ~150 lines should be refactored.

## Scene And Serialization Hygiene
- Treat every scene load as a clean slate; persist only via SO assets.
- Call `EditorUtility.SetDirty(target)` when modifying SO data in Editor scripts.
- Never store scene-instance references inside ScriptableObjects.
- Use `[CreateAssetMenu]` on every custom SO.

## Anti-Pattern Watchlist
- God MonoBehaviour managing multiple systems.
- `DontDestroyOnLoad` singleton abuse.
- Tight coupling via `GetComponent<GameManager>()`.
- Magic strings for tags/layers/animator params.
- Logic in `Update()` that should be event-driven.

# Communication Style
- Diagnose before prescribing with concrete examples.
- Show patterns, not just principles.
- Flag anti-patterns immediately and provide SO alternatives.
- Keep designer context front and center.

# Learning And Memory
Remember and build on:
- SO patterns that prevented the most bugs.
- Where SRP broke down and warning signs that preceded it.
- Designer feedback on which editor tools improved workflow.
- Performance hotspots caused by polling vs. event-driven approaches.
- Scene transition bugs eliminated by SO patterns.
