"""Tests for LLMConfig.from_env and the build_kwargs routing."""

from __future__ import annotations

import json

import pytest

from agency.llm import AnthropicLLM, LLMConfig


def test_from_env_reads_all_fields(monkeypatch):
    monkeypatch.setenv("AGENCY_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("AGENCY_PLANNER_MODEL", "claude-haiku-4-5")
    monkeypatch.setenv("AGENCY_MAX_TOKENS", "8000")
    monkeypatch.setenv("AGENCY_TASK_BUDGET", "50000")
    monkeypatch.setenv("AGENCY_MCP_SERVERS", json.dumps([
        {"type": "url", "name": "github", "url": "https://api.githubcopilot.com/mcp/"}
    ]))
    cfg = LLMConfig.from_env()
    assert cfg.model == "claude-sonnet-4-6"
    assert cfg.planner_model == "claude-haiku-4-5"
    assert cfg.max_tokens == 8000
    assert cfg.task_budget_tokens == 50000
    assert cfg.mcp_servers[0]["name"] == "github"


def test_from_env_ignores_malformed_values(monkeypatch):
    monkeypatch.setenv("AGENCY_MAX_TOKENS", "not-an-int")
    monkeypatch.setenv("AGENCY_MCP_SERVERS", "{not json}")
    cfg = LLMConfig.from_env()
    # Defaults kick in instead of crashing.
    assert cfg.max_tokens == LLMConfig().max_tokens
    assert cfg.mcp_servers == []


def test_build_kwargs_plain_path():
    llm = AnthropicLLM(LLMConfig())
    kwargs, use_beta = llm._build_kwargs(
        system="hi",
        messages=[{"role": "user", "content": "hello"}],
        tools=None, model=None, max_tokens=None, thinking=None,
    )
    assert use_beta is False
    assert "mcp_servers" not in kwargs
    assert "output_config" not in kwargs


def test_build_kwargs_adds_task_budget_and_beta():
    llm = AnthropicLLM(LLMConfig(task_budget_tokens=40_000))
    kwargs, use_beta = llm._build_kwargs(
        system="hi", messages=[], tools=None, model=None, max_tokens=None, thinking=None,
    )
    assert use_beta is True
    assert kwargs["output_config"]["task_budget"] == {"type": "tokens", "total": 40_000}
    assert "task-budgets-2026-03-13" in kwargs["betas"]


def test_build_kwargs_below_minimum_task_budget_is_ignored():
    llm = AnthropicLLM(LLMConfig(task_budget_tokens=5_000))
    kwargs, use_beta = llm._build_kwargs(
        system="hi", messages=[], tools=None, model=None, max_tokens=None, thinking=None,
    )
    assert use_beta is False
    assert "output_config" not in kwargs


def test_build_kwargs_adds_mcp_servers_and_beta():
    servers = [{"type": "url", "name": "gh", "url": "https://example.com/mcp/"}]
    llm = AnthropicLLM(LLMConfig(mcp_servers=servers))
    kwargs, use_beta = llm._build_kwargs(
        system="hi", messages=[], tools=None, model=None, max_tokens=None, thinking=None,
    )
    assert use_beta is True
    assert kwargs["mcp_servers"] == servers
    assert "mcp-client-2025-11-20" in kwargs["betas"]


def test_build_kwargs_appends_web_search_tool_when_enabled():
    llm = AnthropicLLM(LLMConfig(enable_web_search=True))
    kwargs, _ = llm._build_kwargs(
        system="hi", messages=[],
        tools=[{"name": "custom", "description": "x", "input_schema": {"type": "object"}}],
        model=None, max_tokens=None, thinking=None,
    )
    names = [t.get("name") or t.get("type") for t in kwargs["tools"]]
    assert "custom" in names
    assert any(t.get("type") == "web_search_20260209" for t in kwargs["tools"])


def test_build_kwargs_appends_code_execution_tool_when_enabled():
    llm = AnthropicLLM(LLMConfig(enable_code_execution=True))
    kwargs, _ = llm._build_kwargs(
        system="hi", messages=[], tools=None, model=None, max_tokens=None, thinking=None,
    )
    assert any(t.get("type") == "code_execution_20260120" for t in kwargs["tools"])


def test_from_env_reads_feature_flags(monkeypatch):
    monkeypatch.setenv("AGENCY_ENABLE_WEB_SEARCH", "1")
    monkeypatch.setenv("AGENCY_ENABLE_CODE_EXECUTION", "yes")
    cfg = LLMConfig.from_env()
    assert cfg.enable_web_search is True
    assert cfg.enable_code_execution is True
