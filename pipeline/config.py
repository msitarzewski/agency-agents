"""
Model configuration and tier definitions.

Claude Opus supervises. AWS Bedrock models do the work.
Cheap/fast models are preferred; heavier models are used only when the
supervisor decides the task warrants it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Model tiers – ordered cheapest-first
# ---------------------------------------------------------------------------

class ModelTier(str, Enum):
    FREE_FAST = "free_fast"
    FREE_MEDIUM = "free_medium"
    FREE_HEAVY = "free_heavy"
    PAID_SUPERVISOR = "paid_supervisor"


@dataclass(frozen=True)
class ModelSpec:
    """A single model available in the pipeline."""
    name: str                 # Bedrock model ID or Anthropic model id
    tier: ModelTier
    provider: str             # "bedrock" | "anthropic"
    context_window: int = 8192
    strengths: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Default model catalogue – uses AWS Bedrock foundation models
# ---------------------------------------------------------------------------

AWS_BEDROCK_REGION = os.getenv("AWS_BEDROCK_REGION", "us-east-1")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

DEFAULT_MODELS: list[ModelSpec] = [
    # --- Fast (cheap, low-latency Bedrock models) ---
    ModelSpec(
        name="amazon.nova-micro-v1:0",
        tier=ModelTier.FREE_FAST,
        provider="bedrock",
        context_window=128000,
        strengths=("code", "general", "planning", "fast"),
    ),
    ModelSpec(
        name="amazon.nova-lite-v1:0",
        tier=ModelTier.FREE_FAST,
        provider="bedrock",
        context_window=300000,
        strengths=("general", "reasoning", "content"),
    ),
    ModelSpec(
        name="mistral.mistral-small-2402-v1:0",
        tier=ModelTier.FREE_FAST,
        provider="bedrock",
        context_window=32768,
        strengths=("code", "math", "reasoning"),
    ),
    ModelSpec(
        name="meta.llama3-1-8b-instruct-v1:0",
        tier=ModelTier.FREE_FAST,
        provider="bedrock",
        context_window=131072,
        strengths=("code", "debugging", "fast"),
    ),

    # --- Medium (higher quality, moderate cost) ---
    ModelSpec(
        name="anthropic.claude-3-5-haiku-20241022-v1:0",
        tier=ModelTier.FREE_MEDIUM,
        provider="bedrock",
        context_window=200000,
        strengths=("code", "analysis", "planning", "architecture"),
    ),
    ModelSpec(
        name="amazon.nova-pro-v1:0",
        tier=ModelTier.FREE_MEDIUM,
        provider="bedrock",
        context_window=300000,
        strengths=("general", "reasoning", "content", "summarisation"),
    ),
    ModelSpec(
        name="meta.llama3-1-70b-instruct-v1:0",
        tier=ModelTier.FREE_MEDIUM,
        provider="bedrock",
        context_window=131072,
        strengths=("reasoning", "strategy", "content", "analysis"),
    ),

    # --- Heavy (strongest Bedrock models, higher cost) ---
    ModelSpec(
        name="anthropic.claude-sonnet-4-20250514-v1:0",
        tier=ModelTier.FREE_HEAVY,
        provider="bedrock",
        context_window=200000,
        strengths=("code", "architecture", "security", "review"),
    ),
    ModelSpec(
        name="mistral.mistral-large-2402-v1:0",
        tier=ModelTier.FREE_HEAVY,
        provider="bedrock",
        context_window=32768,
        strengths=("general", "reasoning", "multilingual", "content"),
    ),

    # --- Supervisor – only used for orchestration decisions ---
    ModelSpec(
        name="claude-opus-4-6",
        tier=ModelTier.PAID_SUPERVISOR,
        provider="anthropic",
        context_window=200000,
        strengths=("supervision", "routing", "quality-gate", "planning"),
    ),
]


# ---------------------------------------------------------------------------
# Task-type → preferred strengths mapping
# ---------------------------------------------------------------------------

TASK_STRENGTH_MAP: dict[str, list[str]] = {
    # Discovery
    "market_research":    ["general", "content", "analysis"],
    "user_research":      ["general", "reasoning", "analysis"],
    "trend_analysis":     ["general", "analysis", "reasoning"],
    "compliance_review":  ["reasoning", "analysis"],
    "tool_evaluation":    ["code", "analysis", "reasoning"],

    # Strategy
    "project_planning":   ["planning", "reasoning"],
    "architecture":       ["architecture", "code", "reasoning"],
    "ux_strategy":        ["general", "reasoning", "planning"],
    "budgeting":          ["math", "reasoning"],

    # Scaffold
    "devops_setup":       ["code", "architecture"],
    "frontend_scaffold":  ["code", "fast"],
    "backend_scaffold":   ["code", "architecture"],
    "infra_setup":        ["code", "architecture"],

    # Build
    "frontend_dev":       ["code", "fast"],
    "backend_dev":        ["code", "architecture"],
    "mobile_dev":         ["code", "fast"],
    "ai_ml_dev":          ["code", "reasoning", "math"],
    "api_dev":            ["code", "fast"],
    "testing":            ["code", "debugging"],
    "code_review":        ["code", "review", "security"],
    "prototyping":        ["code", "fast"],

    # Harden
    "security_audit":     ["security", "code", "review"],
    "performance_test":   ["code", "analysis"],
    "accessibility_test": ["code", "analysis"],
    "documentation":      ["content", "general"],

    # Launch
    "content_creation":   ["content", "general"],
    "seo_optimization":   ["content", "general"],
    "social_media":       ["content", "general"],
    "analytics_setup":    ["code", "analysis"],

    # Operate
    "monitoring":         ["code", "analysis"],
    "incident_response":  ["code", "debugging", "reasoning"],
    "feedback_analysis":  ["general", "analysis"],
    "reporting":          ["general", "summarisation", "content"],
}


# ---------------------------------------------------------------------------
# Agent → task-type mapping  (used by supervisor for routing)
# ---------------------------------------------------------------------------

AGENT_TASK_TYPE: dict[str, str] = {
    # Discovery
    "Trend Researcher":        "trend_analysis",
    "Feedback Synthesizer":    "user_research",
    "UX Researcher":           "user_research",
    "Analytics Reporter":      "reporting",
    "Legal Compliance Checker": "compliance_review",
    "Tool Evaluator":          "tool_evaluation",

    # Strategy
    "Studio Producer":         "project_planning",
    "Senior Project Manager":  "project_planning",
    "Sprint Prioritizer":      "project_planning",
    "UX Architect":            "ux_strategy",
    "Brand Guardian":          "ux_strategy",
    "Backend Architect":       "architecture",
    "Software Architect":      "architecture",
    "AI Engineer":             "ai_ml_dev",
    "Finance Tracker":         "budgeting",

    # Scaffold
    "DevOps Automator":        "devops_setup",
    "Frontend Developer":      "frontend_scaffold",
    "Infrastructure Maintainer": "infra_setup",
    "Studio Operations":       "project_planning",

    # Build
    "Senior Developer":        "backend_dev",
    "Mobile App Builder":      "mobile_dev",
    "Rapid Prototyper":        "prototyping",
    "API Tester":              "testing",
    "Evidence Collector":      "testing",
    "Test Results Analyzer":   "testing",
    "Performance Benchmarker": "performance_test",
    "Code Reviewer":           "code_review",
    "Database Optimizer":      "backend_dev",
    "Git Workflow Master":     "code_review",
    "SRE":                     "monitoring",
    "Data Engineer":           "backend_dev",

    # Harden
    "Reality Checker":         "testing",
    "Security Engineer":       "security_audit",
    "Accessibility Auditor":   "accessibility_test",
    "Technical Writer":        "documentation",
    "Threat Detection Engineer": "security_audit",

    # Launch
    "Content Creator":         "content_creation",
    "Social Media Strategist": "social_media",
    "Growth Hacker":           "seo_optimization",
    "App Store Optimizer":     "seo_optimization",
    "SEO Specialist":          "seo_optimization",
    "Support Responder":       "reporting",
    "Project Shepherd":        "project_planning",
    "Experiment Tracker":      "analytics_setup",

    # Operate
    "Incident Response Commander": "incident_response",
    "Executive Summary Generator": "reporting",

    # Spatial / Game / Specialized
    "XR Interface Architect":       "architecture",
    "XR Immersive Developer":       "frontend_dev",
    "visionOS Spatial Engineer":    "mobile_dev",
    "macOS Spatial Metal Engineer":  "frontend_dev",
    "Agents Orchestrator":          "project_planning",
    "MCP Builder":                  "backend_dev",
    "LSP Index Engineer":           "backend_dev",
    "Embedded Firmware Engineer":   "backend_dev",
    "Solidity Smart Contract Engineer": "backend_dev",
    "Blockchain Security Auditor":  "security_audit",
    "Compliance Auditor":           "compliance_review",
    "Image Prompt Engineer":        "content_creation",
    "Visual Storyteller":           "content_creation",
    "Whimsy Injector":              "content_creation",
    "UI Designer":                  "ux_strategy",
    "Inclusive Visuals Specialist":  "accessibility_test",
}


@dataclass
class PipelineConfig:
    """Runtime configuration for the pipeline."""
    models: list[ModelSpec] = field(default_factory=lambda: list(DEFAULT_MODELS))
    aws_bedrock_region: str = AWS_BEDROCK_REGION
    anthropic_api_key: str = ANTHROPIC_API_KEY
    agent_specs_root: str = ""  # set to repo root at startup
    max_retries: int = 3
    verbose: bool = False
