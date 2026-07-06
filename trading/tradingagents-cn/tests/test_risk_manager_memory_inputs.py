import unittest

from tradingagents.agents.managers.risk_manager import create_risk_manager


class _DummyLLM:
    def invoke(self, prompt):
        class _Resp:
            content = "ok"

        return _Resp()


class _MemorySpy:
    def __init__(self):
        self.last_query = None

    def get_memories(self, query, n_matches=2):
        self.last_query = query
        return []


class RiskManagerMemoryInputTests(unittest.TestCase):
    def test_risk_manager_uses_fundamentals_report_in_memory_query(self):
        memory = _MemorySpy()
        llm = _DummyLLM()
        node = create_risk_manager(llm, memory)

        state = {
            "company_of_interest": "0700.HK",
            "risk_debate_state": {
                "history": "debate history",
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "latest_speaker": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "count": 0,
            },
            "market_report": "MARKET_REPORT",
            "sentiment_report": "SENTIMENT_REPORT",
            "news_report": "NEWS_REPORT",
            "fundamentals_report": "FUNDAMENTALS_REPORT",
            "investment_plan": "PLAN",
        }

        node(state)

        self.assertIsNotNone(memory.last_query)
        self.assertIn("FUNDAMENTALS_REPORT", memory.last_query)


if __name__ == "__main__":
    unittest.main()
