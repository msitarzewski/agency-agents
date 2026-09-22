#!/usr/bin/env python3
"""Retrieval quality check for the Hermes Agency router's search tool.

The router exists so Hermes can pick one specialist out of the whole roster
without putting all of them in the prompt. That only works if the ranking is
any good, and ranking is the one thing the other Hermes tests never looked at.

JUDGMENTS below is a hand-written set: a plausible user question paired with
the slugs that are a reasonable answer. It is not a benchmark, it is a floor —
it catches the case where a scoring change makes the roster unsearchable. The
thresholds are set a little under what the current scorer achieves so ordinary
roster growth does not fail the build; a real regression drops well past them.

Run it directly to see the full ranking report:
    python3 scripts/test-hermes-search.py            # check thresholds
    python3 scripts/test-hermes-search.py --report   # print every query's top 3

It builds the plugin into a temp directory the way check-hermes-plugin.py does,
so it needs no prior convert.sh run and leaves the tree alone.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build-hermes-plugin.py"

# query -> slugs that are a defensible answer. Several entries list more than
# one because the roster genuinely has more than one right specialist.
JUDGMENTS: list[tuple[str, list[str]]] = [
    ("my postgres queries are slow",
     ["database-optimizer", "database-reliability-engineer"]),
    ("help me improve our customer onboarding emails",
     ["email-marketing-strategist"]),
    ("i want to ship a mobile app to the app store",
     ["mobile-release-engineer", "app-store-optimizer"]),
    ("how do I make my site rank on google",
     ["seo-specialist"]),
    ("write release notes and a changelog",
     ["technical-writer"]),
    ("accessibility audit of our checkout flow",
     ["accessibility-auditor", "section-508-accessibility-specialist"]),
    ("design a public REST API with versioning and rate limits",
     ["api-platform-engineer"]),
    ("review my terraform for security problems",
     ["cloud-security-architect", "application-security-engineer", "devops-automator"]),
    ("kubernetes pods keep crashlooping in production",
     ["sre-site-reliability-engineer", "devops-automator", "incident-response-commander"]),
    ("set up stripe subscriptions and handle webhooks",
     ["payments-billing-engineer"]),
    ("our elasticsearch results are not relevant",
     ["search-relevance-engineer"]),
    ("translate the app into german and arabic",
     ["internationalization-engineer"]),
    ("build an HLS video player with adaptive bitrate",
     ["video-streaming-engineer"]),
    ("write unit tests with playwright",
     ["test-automation-engineer"]),
    ("we need a threat model for the new service",
     ["security-architect", "application-security-engineer"]),
    ("reduce our AWS bill",
     ["finops-engineer"]),
    ("someone to run our sprint planning",
     ["sprint-prioritizer", "senior-project-manager"]),
    ("make a tiktok video go viral",
     ["tiktok-strategist"]),
    ("chunking and reranking for our RAG pipeline",
     ["rag-pipeline-engineer"]),
    ("sign and notarize our electron app",
     ["desktop-app-engineer"]),
    ("our LCP is 4 seconds on wordpress",
     ["wordpress-performance-engineer"]),
    ("set up SSO with okta and SCIM provisioning",
     ["identity-access-engineer"]),
    ("who can help me write a press release",
     ["pr-communications-manager"]),
    ("i need a smart contract audited",
     ["blockchain-security-auditor", "solidity-smart-contract-engineer"]),
    ("collaborative editing with CRDTs",
     ["realtime-collaboration-engineer"]),
]

# Floors, not targets. Measured on the roster at the time of writing:
# recall@1 0.80, recall@3 0.92, and 47 of 279 agents returned per query.
MIN_RECALL_AT_1 = 0.68
MIN_RECALL_AT_3 = 0.84
MAX_MEAN_RESULTS_FRACTION = 0.35


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"could not load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The plugin reads its roster from a sibling data/agents.json, so the temp
# directory has to outlive the module. It is cleaned up at interpreter exit.
_TMP = tempfile.TemporaryDirectory()


def load_router():
    builder = _load("agency_agents_hermes_builder", BUILDER)
    out_dir = Path(_TMP.name) / "hermes"
    builder.build(ROOT, out_dir)
    return _load("agency_router_search",
                 out_dir / builder.PLUGIN_NAME / "__init__.py")


def rank(module, query: str) -> list[tuple[float, dict]]:
    module._build_index()
    terms = {t: module._expansions(t) for t in module._query_terms(query)}
    lowered = query.lower()
    scored = []
    for agent in module._load_agents():
        score = module._score(agent, terms, lowered)
        if score > 0:
            scored.append((score, agent))
    scored.sort(key=lambda item: (-item[0], item[1]["division"], item[1]["slug"]))
    return scored


def measure(module):
    roster = len(module._load_agents())
    at1 = at3 = 0
    returned = 0
    rows = []
    for query, wanted in JUDGMENTS:
        results = rank(module, query)
        returned += len(results)
        position = None
        for i, (_score, agent) in enumerate(results, 1):
            if agent["slug"] in wanted:
                position = i
                break
        if position == 1:
            at1 += 1
        if position is not None and position <= 3:
            at3 += 1
        rows.append((query, wanted, position, len(results),
                     [a["name"] for _s, a in results[:3]]))
    n = len(JUDGMENTS)
    return {
        "roster": roster,
        "recall_at_1": at1 / n,
        "recall_at_3": at3 / n,
        "mean_results": returned / n,
        "rows": rows,
    }


class SearchQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_router()
        cls.stats = measure(cls.module)

    def test_slugs_in_the_judgment_set_still_exist(self):
        known = {a["slug"] for a in self.module._load_agents()}
        missing = sorted({s for _q, slugs in JUDGMENTS for s in slugs} - known)
        self.assertEqual(missing, [], "judgment set references agents that are gone")

    def test_top_hit_is_usually_right(self):
        self.assertGreaterEqual(
            self.stats["recall_at_1"], MIN_RECALL_AT_1,
            f"recall@1 fell to {self.stats['recall_at_1']:.2f}")

    def test_right_answer_is_in_the_top_three(self):
        self.assertGreaterEqual(
            self.stats["recall_at_3"], MIN_RECALL_AT_3,
            f"recall@3 fell to {self.stats['recall_at_3']:.2f}")

    def test_search_narrows_the_roster(self):
        """A search that returns almost everything has not searched anything."""
        fraction = self.stats["mean_results"] / self.stats["roster"]
        self.assertLessEqual(
            fraction, MAX_MEAN_RESULTS_FRACTION,
            f"search returns {self.stats['mean_results']:.0f} of "
            f"{self.stats['roster']} agents on average")

    def test_a_query_term_does_not_match_a_word_it_only_sits_inside(self):
        """'go' is not a hit on Godot, 'ai' is not a hit on Email."""
        module = self.module
        module._build_index()
        for term, slug in (("go", "godot-multiplayer-engineer"),
                           ("ai", "email-marketing-strategist"),
                           ("art", "drupal-shopping-cart-engineer")):
            agent = next((a for a in module._load_agents() if a["slug"] == slug), None)
            if agent is None:
                continue
            score = module._score(agent, {term: module._expansions(term)}, term)
            self.assertEqual(
                score, 0.0,
                f"{slug} still scores on {term!r}, which only appears inside a longer word")

    def test_a_query_of_only_stop_words_does_not_crash(self):
        module = self.module
        results = rank(module, "how do I do this")
        self.assertIsInstance(results, list)


def report():
    module = load_router()
    stats = measure(module)
    print(f"roster: {stats['roster']} agents, {len(JUDGMENTS)} judgment queries\n")
    for query, wanted, position, count, top in stats["rows"]:
        flag = "ok  " if position is not None and position <= 3 else "MISS"
        print(f"  [{flag} rank={str(position):<5} results={count:<4}] {query}")
        print(f"         want: {', '.join(wanted)}")
        print(f"         got:  {', '.join(top)}")
    print(f"\n  recall@1     {stats['recall_at_1']:.2f}   (floor {MIN_RECALL_AT_1})")
    print(f"  recall@3     {stats['recall_at_3']:.2f}   (floor {MIN_RECALL_AT_3})")
    print(f"  mean results {stats['mean_results']:.0f} of {stats['roster']}"
          f"   (ceiling {MAX_MEAN_RESULTS_FRACTION * stats['roster']:.0f})")


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
    else:
        unittest.main()
