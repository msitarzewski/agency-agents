#!/usr/bin/env python3
"""Behavior checks for the generated Hermes Agency router plugin."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "integrations" / "hermes" / "agency-agents-router" / "__init__.py"


class State(str, Enum):
    RUNNING = "RUNNING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FakeRequest:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeLifecycle:
    def __init__(self, *, waits=None, result=None, launch_error=None):
        self.waits = list(waits or [terminal(State.SUCCEEDED, completed=True)])
        self.result_value = result or child_result(State.SUCCEEDED, summary="ROUTER_OK")
        self.launch_error = launch_error
        self.request = None
        self.wait_timeouts = []
        self.cancelled = False

    def launch(self, request):
        if self.launch_error:
            raise self.launch_error
        self.request = request
        return SimpleNamespace(subagent_id="child-1")

    def wait(self, handle, *, timeout_seconds=None):
        del handle
        self.wait_timeouts.append(timeout_seconds)
        return self.waits.pop(0)

    def cancel(self, handle, *, reason):
        del handle, reason
        self.cancelled = True
        return SimpleNamespace(accepted=True)

    def result(self, handle):
        del handle
        return self.result_value


class FakeContext:
    def __init__(self, lifecycle):
        self.subagent_lifecycle = lifecycle
        self.tools = {}

    def register_tool(self, *, name, schema, handler, **kwargs):
        del kwargs
        self.tools[name] = (schema, handler)


def terminal(state, *, completed=False, timed_out=False):
    return SimpleNamespace(state=state, completed=completed, timed_out=timed_out)


def child_result(state, *, ready=True, summary=None, error=None):
    return SimpleNamespace(
        ready=ready,
        terminal_state=state,
        summary=summary,
        structured_payload={"ok": True} if state == State.SUCCEEDED else None,
        error_message=error,
        error_classification=None,
    )


def load_plugin(lifecycle):
    agent_module = types.ModuleType("agent")
    lifecycle_module = types.ModuleType("agent.subagent_lifecycle")
    setattr(lifecycle_module, "SubagentLaunchRequest", FakeRequest)
    sys.modules["agent"] = agent_module
    sys.modules["agent.subagent_lifecycle"] = lifecycle_module

    spec = importlib.util.spec_from_file_location("agency_router_under_test", PLUGIN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    context = FakeContext(lifecycle)
    module.register(context)
    return module, context


class DelegateBehaviorTests(unittest.TestCase):
    def invoke(self, lifecycle, slug="ux-architect"):
        module, context = load_plugin(lifecycle)
        schema, handler = context.tools["agency_agents_delegate"]
        payload = json.loads(handler({"slug": slug, "task": "Return ROUTER_OK"}))
        return module, schema, payload

    def test_success_returns_child_result_without_toolsets_option(self):
        lifecycle = FakeLifecycle()
        _, schema, payload = self.invoke(lifecycle)
        self.assertTrue(payload["delegated"])
        self.assertEqual(payload["result"], "ROUTER_OK")
        self.assertNotIn("toolsets", schema["parameters"]["properties"])
        self.assertEqual(lifecycle.wait_timeouts, [330])

    def test_failed_child_returns_safe_fallback(self):
        lifecycle = FakeLifecycle(
            result=child_result(State.FAILED, error="child failed")
        )
        _, _, payload = self.invoke(lifecycle)
        self.assertFalse(payload["delegated"])
        self.assertIn("Return ROUTER_OK", payload["prompt"])

    def test_launch_exception_returns_safe_fallback(self):
        lifecycle = FakeLifecycle(launch_error=RuntimeError("launch failed"))
        _, _, payload = self.invoke(lifecycle)
        self.assertFalse(payload["delegated"])
        self.assertIn("launch failed", payload["warning"])

    def test_unconfirmed_cancellation_is_truthfully_pending_without_fallback(self):
        lifecycle = FakeLifecycle(waits=[
            terminal(State.RUNNING, timed_out=True),
            terminal(State.CANCEL_REQUESTED),
        ])
        _, _, payload = self.invoke(lifecycle)
        self.assertTrue(payload["delegated"])
        self.assertTrue(payload["pending"])
        self.assertNotIn("prompt", payload)
        self.assertTrue(lifecycle.cancelled)
        self.assertEqual(lifecycle.wait_timeouts, [330, 30])

    def test_confirmed_cancellation_returns_fallback(self):
        lifecycle = FakeLifecycle(
            waits=[
                terminal(State.RUNNING, timed_out=True),
                terminal(State.CANCELLED, completed=True),
            ],
            result=child_result(State.CANCELLED, error="cancelled"),
        )
        _, _, payload = self.invoke(lifecycle)
        self.assertFalse(payload["delegated"])
        self.assertIn("Return ROUTER_OK", payload["prompt"])

    def test_large_specialist_context_is_marked_and_bounded(self):
        lifecycle = FakeLifecycle()
        module, _, payload = self.invoke(
            lifecycle, slug="healthcare-marketing-compliance-specialist"
        )
        self.assertTrue(payload["delegated"])
        request = lifecycle.request
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(len(request.context), 32_000)
        self.assertTrue(request.context.endswith(module._TRUNCATION_MARKER))


if __name__ == "__main__":
    unittest.main()
