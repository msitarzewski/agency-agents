"""
测试辩论流程模拟
验证投资辩论和风险讨论的轮次控制是否正确
"""
import pytest
from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.agents.utils.agent_states import AgentState, InvestDebateState, RiskDebateState


class TestInvestmentDebateFlow:
    """测试投资辩论流程"""

    def test_level_4_investment_debate_2_rounds(self):
        """测试4级深度分析的投资辩论（2轮）"""
        logic = ConditionalLogic(max_debate_rounds=2, max_risk_discuss_rounds=2)
        
        # 模拟投资辩论状态
        state = {
            "investment_debate_state": {
                "count": 0,
                "current_response": "Bull Researcher"
            }
        }
        
        # 第1轮
        # Bull -> Bear
        assert logic.should_continue_debate(state) == "Bear Researcher"
        state["investment_debate_state"]["count"] = 1
        state["investment_debate_state"]["current_response"] = "Bear Researcher"  # 更新为Bear

        # Bear -> Bull
        assert logic.should_continue_debate(state) == "Bull Researcher"
        state["investment_debate_state"]["count"] = 2
        state["investment_debate_state"]["current_response"] = "Bull Researcher"  # 更新为Bull

        # 第2轮
        # Bull -> Bear
        assert logic.should_continue_debate(state) == "Bear Researcher"
        state["investment_debate_state"]["count"] = 3
        state["investment_debate_state"]["current_response"] = "Bear Researcher"  # 更新为Bear

        # Bear -> Research Manager (结束)
        # count = 4 >= 2 * 2 = 4
        state["investment_debate_state"]["count"] = 4
        assert logic.should_continue_debate(state) == "Research Manager"

    def test_level_5_investment_debate_3_rounds(self):
        """测试5级全面分析的投资辩论（3轮）"""
        logic = ConditionalLogic(max_debate_rounds=3, max_risk_discuss_rounds=3)
        
        state = {
            "investment_debate_state": {
                "count": 0,
                "current_response": "Bull Researcher"
            }
        }
        
        # 第1轮：Bull -> Bear -> Bull
        for i in range(2):
            assert logic.should_continue_debate(state) in ["Bear Researcher", "Bull Researcher"]
            state["investment_debate_state"]["count"] = i + 1
        
        # 第2轮：Bear -> Bull -> Bear
        for i in range(2, 4):
            assert logic.should_continue_debate(state) in ["Bear Researcher", "Bull Researcher"]
            state["investment_debate_state"]["count"] = i + 1
        
        # 第3轮：Bull -> Bear
        for i in range(4, 6):
            assert logic.should_continue_debate(state) in ["Bear Researcher", "Bull Researcher"]
            state["investment_debate_state"]["count"] = i + 1
        
        # count = 6 >= 2 * 3 = 6，结束
        assert logic.should_continue_debate(state) == "Research Manager"


class TestRiskDebateFlow:
    """测试风险讨论流程"""

    def test_level_4_risk_debate_2_rounds(self):
        """测试4级深度分析的风险讨论（2轮）"""
        logic = ConditionalLogic(max_debate_rounds=2, max_risk_discuss_rounds=2)
        
        # 模拟风险辩论状态
        state = {
            "risk_debate_state": {
                "count": 0,
                "latest_speaker": "Risky Analyst"
            }
        }
        
        # 第1轮：Risky -> Safe -> Neutral
        # Risky -> Safe
        assert logic.should_continue_risk_analysis(state) == "Safe Analyst"
        state["risk_debate_state"]["count"] = 1
        state["risk_debate_state"]["latest_speaker"] = "Safe Analyst"  # 更新为Safe

        # Safe -> Neutral
        assert logic.should_continue_risk_analysis(state) == "Neutral Analyst"
        state["risk_debate_state"]["count"] = 2
        state["risk_debate_state"]["latest_speaker"] = "Neutral Analyst"  # 更新为Neutral

        # Neutral -> Risky
        assert logic.should_continue_risk_analysis(state) == "Risky Analyst"
        state["risk_debate_state"]["count"] = 3
        state["risk_debate_state"]["latest_speaker"] = "Risky Analyst"  # 更新为Risky

        # 第2轮：Risky -> Safe -> Neutral
        # Risky -> Safe
        assert logic.should_continue_risk_analysis(state) == "Safe Analyst"
        state["risk_debate_state"]["count"] = 4
        state["risk_debate_state"]["latest_speaker"] = "Safe Analyst"  # 更新为Safe

        # Safe -> Neutral
        assert logic.should_continue_risk_analysis(state) == "Neutral Analyst"
        state["risk_debate_state"]["count"] = 5
        state["risk_debate_state"]["latest_speaker"] = "Neutral Analyst"  # 更新为Neutral

        # Neutral -> Risk Judge (结束)
        # count = 6 >= 3 * 2 = 6
        state["risk_debate_state"]["count"] = 6
        assert logic.should_continue_risk_analysis(state) == "Risk Judge"

    def test_level_5_risk_debate_3_rounds(self):
        """测试5级全面分析的风险讨论（3轮）"""
        logic = ConditionalLogic(max_debate_rounds=3, max_risk_discuss_rounds=3)
        
        state = {
            "risk_debate_state": {
                "count": 0,
                "latest_speaker": "Risky Analyst"
            }
        }
        
        speakers = ["Risky Analyst", "Safe Analyst", "Neutral Analyst"]
        expected_next = ["Safe Analyst", "Neutral Analyst", "Risky Analyst"]
        
        # 3轮，每轮3个发言者
        for round_num in range(3):
            for speaker_idx in range(3):
                current_count = round_num * 3 + speaker_idx
                state["risk_debate_state"]["count"] = current_count
                state["risk_debate_state"]["latest_speaker"] = speakers[speaker_idx]
                
                if current_count < 9:  # 3 * 3 = 9
                    next_speaker = logic.should_continue_risk_analysis(state)
                    assert next_speaker == expected_next[speaker_idx], \
                        f"轮次{round_num+1}，发言者{speaker_idx+1}，期望下一个是{expected_next[speaker_idx]}，实际是{next_speaker}"
        
        # count = 9 >= 3 * 3 = 9，结束
        state["risk_debate_state"]["count"] = 9
        assert logic.should_continue_risk_analysis(state) == "Risk Judge"


class TestDebateRoundsCalculation:
    """测试辩论轮次计算"""

    @pytest.mark.parametrize("max_debate_rounds,expected_total_count", [
        (1, 2),   # 1轮 = 2次发言（Bull + Bear）
        (2, 4),   # 2轮 = 4次发言
        (3, 6),   # 3轮 = 6次发言
        (5, 10),  # 5轮 = 10次发言
    ])
    def test_investment_debate_total_count(self, max_debate_rounds, expected_total_count):
        """测试投资辩论的总发言次数"""
        logic = ConditionalLogic(max_debate_rounds=max_debate_rounds)
        
        state = {
            "investment_debate_state": {
                "count": expected_total_count - 1,
                "current_response": "Bull Researcher"
            }
        }
        
        # 未达到阈值，继续辩论
        assert logic.should_continue_debate(state) in ["Bear Researcher", "Bull Researcher"]
        
        # 达到阈值，结束辩论
        state["investment_debate_state"]["count"] = expected_total_count
        assert logic.should_continue_debate(state) == "Research Manager"

    @pytest.mark.parametrize("max_risk_discuss_rounds,expected_total_count", [
        (1, 3),   # 1轮 = 3次发言（Risky + Safe + Neutral）
        (2, 6),   # 2轮 = 6次发言
        (3, 9),   # 3轮 = 9次发言
        (5, 15),  # 5轮 = 15次发言
    ])
    def test_risk_debate_total_count(self, max_risk_discuss_rounds, expected_total_count):
        """测试风险讨论的总发言次数"""
        logic = ConditionalLogic(max_risk_discuss_rounds=max_risk_discuss_rounds)
        
        state = {
            "risk_debate_state": {
                "count": expected_total_count - 1,
                "latest_speaker": "Risky Analyst"
            }
        }
        
        # 未达到阈值，继续讨论
        assert logic.should_continue_risk_analysis(state) in ["Safe Analyst", "Neutral Analyst", "Risky Analyst"]
        
        # 达到阈值，结束讨论
        state["risk_debate_state"]["count"] = expected_total_count
        assert logic.should_continue_risk_analysis(state) == "Risk Judge"


class TestDebateFlowSummary:
    """测试辩论流程总结"""

    def test_level_4_complete_flow(self):
        """测试4级深度分析的完整流程"""
        logic = ConditionalLogic(max_debate_rounds=2, max_risk_discuss_rounds=2)
        
        # 投资辩论：2轮 = 4次发言
        # 风险讨论：2轮 = 6次发言
        
        print("\n4级深度分析流程：")
        print("投资辩论（2轮）：")
        print("  第1轮：Bull -> Bear")
        print("  第2轮：Bull -> Bear")
        print("  总计：4次发言")
        
        print("\n风险讨论（2轮）：")
        print("  第1轮：Risky -> Safe -> Neutral")
        print("  第2轮：Risky -> Safe -> Neutral")
        print("  总计：6次发言")
        
        assert logic.max_debate_rounds == 2
        assert logic.max_risk_discuss_rounds == 2

    def test_level_5_complete_flow(self):
        """测试5级全面分析的完整流程"""
        logic = ConditionalLogic(max_debate_rounds=3, max_risk_discuss_rounds=3)
        
        # 投资辩论：3轮 = 6次发言
        # 风险讨论：3轮 = 9次发言
        
        print("\n5级全面分析流程：")
        print("投资辩论（3轮）：")
        print("  第1轮：Bull -> Bear")
        print("  第2轮：Bull -> Bear")
        print("  第3轮：Bull -> Bear")
        print("  总计：6次发言")
        
        print("\n风险讨论（3轮）：")
        print("  第1轮：Risky -> Safe -> Neutral")
        print("  第2轮：Risky -> Safe -> Neutral")
        print("  第3轮：Risky -> Safe -> Neutral")
        print("  总计：9次发言")
        
        assert logic.max_debate_rounds == 3
        assert logic.max_risk_discuss_rounds == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

