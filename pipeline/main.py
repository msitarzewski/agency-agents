#!/usr/bin/env python3
"""
DreamEngine NEXUS Pipeline — CLI entry point.

Usage:
  python -m pipeline.main --brief "Build a SaaS task manager with auth and billing"
  python -m pipeline.main --brief-file project-brief.txt
  python -m pipeline.main --brief "..." --phases discover,strategize
  python -m pipeline.main --brief "..." --verbose
  python -m pipeline.main --list-agents
  python -m pipeline.main --list-models
  python -m pipeline.main --check-ollama
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Ensure the repo root is on the path
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from pipeline.agents import PHASE_AGENTS, agents_for_phase, load_all_agents
from pipeline.config import DEFAULT_MODELS, PipelineConfig
from pipeline.graph import build_graph
from pipeline.state import PipelineState


def check_ollama(config: PipelineConfig) -> None:
    """Verify Ollama is reachable and list available models."""
    import httpx

    print(f"Checking Ollama at {config.ollama_base_url} ...")
    try:
        resp = httpx.get(f"{config.ollama_base_url}/api/tags", timeout=10.0)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        available = {m["name"] for m in models}
        print(f"  ✓ Ollama is running — {len(models)} models available\n")

        # Check which pipeline models are pulled
        for spec in config.models:
            if spec.provider != "ollama":
                continue
            # Ollama tags can be "qwen2.5:7b" or "qwen2.5:7b-instruct-..."
            base = spec.name.split(":")[0]
            found = any(base in m for m in available)
            icon = "✓" if found else "✗"
            print(f"  {icon} {spec.name:30s} ({spec.tier.value})"
                  f"{'  ← pull with: ollama pull ' + spec.name if not found else ''}")
    except Exception as e:
        print(f"  ✗ Cannot reach Ollama: {e}")
        print(f"    Start it with: ollama serve")
        sys.exit(1)


def list_agents(config: PipelineConfig) -> None:
    """Print all loaded agents grouped by phase."""
    registry = load_all_agents(config.agent_specs_root)
    print(f"\nLoaded {len(registry)} agents from {config.agent_specs_root}\n")

    for phase, names in PHASE_AGENTS.items():
        print(f"  ■ {phase.upper()}")
        for name in names:
            agent = registry.get(name)
            if agent:
                print(f"    {agent.emoji} {agent.name:35s} [{agent.division}]")
            else:
                print(f"    ⚠ {name:35s} [NOT FOUND]")
        print()


def list_models() -> None:
    """Print configured model tiers."""
    print("\nConfigured model tiers (cheapest first):\n")
    for spec in DEFAULT_MODELS:
        print(f"  {spec.tier.value:16s}  {spec.name:30s}  "
              f"({spec.provider})  strengths={list(spec.strengths)}")
    print()


def print_report(state: dict) -> None:
    """Print a human-readable pipeline run report."""
    print("\n" + "=" * 70)
    print("  NEXUS PIPELINE — RUN REPORT")
    print("=" * 70)

    # Messages log
    for msg in state.get("messages", []):
        print(f"  {msg}")

    # Gate verdicts
    print("\n  QUALITY GATES:")
    for v in state.get("gate_verdicts", []):
        icon = "✅" if v["passed"] else "❌"
        print(f"    {icon} {v['phase']:12s}  {v['reason']}")

    # Model usage summary
    results = state.get("results", [])
    tier_counts: dict[str, int] = {}
    model_counts: dict[str, int] = {}
    for r in results:
        tier_counts[r["model_tier"]] = tier_counts.get(r["model_tier"], 0) + 1
        model_counts[r["model_used"]] = model_counts.get(r["model_used"], 0) + 1

    print("\n  MODEL USAGE:")
    for tier, count in sorted(tier_counts.items()):
        print(f"    {tier:16s}  {count} tasks")
    print()
    for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
        print(f"    {model:30s}  {count} tasks")

    # Success rate
    successes = sum(1 for r in results if r["status"] == "success")
    print(f"\n  RESULTS: {successes}/{len(results)} tasks succeeded")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DreamEngine NEXUS Pipeline — AI-driven dev workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--brief", type=str, help="Project brief (inline text)")
    parser.add_argument("--brief-file", type=str, help="Path to project brief file")
    parser.add_argument(
        "--phases", type=str, default=None,
        help="Comma-separated list of phases to run (default: all)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--list-agents", action="store_true", help="List all agents by phase")
    parser.add_argument("--list-models", action="store_true", help="List configured models")
    parser.add_argument("--check-ollama", action="store_true", help="Check Ollama connectivity")
    parser.add_argument(
        "--ollama-url", type=str, default=None,
        help="Ollama base URL (default: http://localhost:11434)",
    )
    parser.add_argument("--output", type=str, default=None, help="Save results JSON to file")

    args = parser.parse_args()

    # --- Logging ---
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    # --- Config ---
    config = PipelineConfig(agent_specs_root=REPO_ROOT)
    if args.ollama_url:
        config.ollama_base_url = args.ollama_url

    # --- Diagnostic commands ---
    if args.check_ollama:
        check_ollama(config)
        return
    if args.list_agents:
        list_agents(config)
        return
    if args.list_models:
        list_models()
        return

    # --- Validate brief ---
    brief = args.brief
    if args.brief_file:
        brief = Path(args.brief_file).read_text(encoding="utf-8")
    if not brief:
        parser.error("Provide --brief or --brief-file")

    # --- Validate API key ---
    if not config.anthropic_api_key:
        print("⚠ ANTHROPIC_API_KEY not set — supervisor calls will fail.")
        print("  Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    # --- Build and run ---
    print("\n🚀 DreamEngine NEXUS Pipeline")
    print(f"   Repo root:  {REPO_ROOT}")
    print(f"   Ollama:     {config.ollama_base_url}")
    print(f"   Phases:     {args.phases or 'all'}")
    print()

    graph = build_graph(config)

    initial_state: PipelineState = {
        "project_brief": brief,
        "repo_root": REPO_ROOT,
        "results": [],
        "gate_verdicts": [],
        "messages": [],
        "current_phase": "",
        "next_phase": "",
        "phase_plan": [],
        "retry_count": 0,
        "should_halt": False,
    }

    # Run the graph
    final_state = graph.invoke(initial_state)

    # Report
    print_report(final_state)

    # Optionally save results
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(final_state, f, indent=2, default=str)
        print(f"\n  Results saved to {args.output}")


if __name__ == "__main__":
    main()
