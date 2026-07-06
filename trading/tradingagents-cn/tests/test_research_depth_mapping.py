"""
测试研究深度映射是否正确
验证前端数字等级到后端中文等级的转换
"""
import pytest
from app.services.simple_analysis_service import create_analysis_config


class TestResearchDepthMapping:
    """测试研究深度映射"""

    def test_level_1_fast(self):
        """测试1级 - 快速分析"""
        config = create_analysis_config(
            research_depth=1,  # 前端传入数字1
            selected_analysts=["market"],
            quick_model="qwen-turbo",
            deep_model="qwen-plus",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 1
        assert config["memory_enabled"] is False
        assert config["research_depth"] == "快速"

    def test_level_2_basic(self):
        """测试2级 - 基础分析"""
        config = create_analysis_config(
            research_depth=2,  # 前端传入数字2
            selected_analysts=["market"],
            quick_model="qwen-turbo",
            deep_model="qwen-plus",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 1
        assert config["memory_enabled"] is True
        assert config["research_depth"] == "基础"

    def test_level_3_standard(self):
        """测试3级 - 标准分析"""
        config = create_analysis_config(
            research_depth=3,  # 前端传入数字3
            selected_analysts=["market"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 2
        assert config["memory_enabled"] is True
        assert config["research_depth"] == "标准"

    def test_level_4_deep(self):
        """测试4级 - 深度分析 (关键测试)"""
        config = create_analysis_config(
            research_depth=4,  # 前端传入数字4
            selected_analysts=["market"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        # 🔥 关键断言：4级应该有2轮辩论
        assert config["max_debate_rounds"] == 2, "4级深度分析应该有2轮辩论"
        assert config["max_risk_discuss_rounds"] == 2, "4级深度分析应该有2轮风险讨论"
        assert config["memory_enabled"] is True
        assert config["research_depth"] == "深度"

    def test_level_5_comprehensive(self):
        """测试5级 - 全面分析"""
        config = create_analysis_config(
            research_depth=5,  # 前端传入数字5
            selected_analysts=["market"],
            quick_model="qwen-max",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        # 🔥 关键断言：5级应该有3轮辩论
        assert config["max_debate_rounds"] == 3, "5级全面分析应该有3轮辩论"
        assert config["max_risk_discuss_rounds"] == 3, "5级全面分析应该有3轮风险讨论"
        assert config["memory_enabled"] is True
        assert config["research_depth"] == "全面"

    def test_chinese_depth_fast(self):
        """测试中文深度 - 快速"""
        config = create_analysis_config(
            research_depth="快速",  # 直接传入中文
            selected_analysts=["market"],
            quick_model="qwen-turbo",
            deep_model="qwen-plus",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 1
        assert config["research_depth"] == "快速"

    def test_chinese_depth_deep(self):
        """测试中文深度 - 深度"""
        config = create_analysis_config(
            research_depth="深度",  # 直接传入中文
            selected_analysts=["market"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 2
        assert config["max_risk_discuss_rounds"] == 2
        assert config["research_depth"] == "深度"

    def test_chinese_depth_comprehensive(self):
        """测试中文深度 - 全面"""
        config = create_analysis_config(
            research_depth="全面",  # 直接传入中文
            selected_analysts=["market"],
            quick_model="qwen-max",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 3
        assert config["max_risk_discuss_rounds"] == 3
        assert config["research_depth"] == "全面"

    def test_string_number_depth(self):
        """测试字符串数字深度"""
        config = create_analysis_config(
            research_depth="4",  # 字符串形式的数字
            selected_analysts=["market"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 2
        assert config["max_risk_discuss_rounds"] == 2
        assert config["research_depth"] == "深度"

    def test_invalid_depth_fallback(self):
        """测试无效深度回退到默认值"""
        config = create_analysis_config(
            research_depth=99,  # 无效的数字
            selected_analysts=["market"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        # 应该回退到标准分析
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 2
        assert config["research_depth"] == "标准"

    def test_debate_rounds_progression(self):
        """测试辩论轮次的递进关系"""
        levels = [1, 2, 3, 4, 5]
        expected_debate_rounds = [1, 1, 1, 2, 3]
        expected_risk_rounds = [1, 1, 2, 2, 3]
        
        for level, expected_debate, expected_risk in zip(levels, expected_debate_rounds, expected_risk_rounds):
            config = create_analysis_config(
                research_depth=level,
                selected_analysts=["market"],
                quick_model="qwen-plus",
                deep_model="qwen-max",
                llm_provider="dashscope",
                market_type="A股"
            )
            
            assert config["max_debate_rounds"] == expected_debate, \
                f"级别{level}的辩论轮次应该是{expected_debate}，实际是{config['max_debate_rounds']}"
            assert config["max_risk_discuss_rounds"] == expected_risk, \
                f"级别{level}的风险讨论轮次应该是{expected_risk}，实际是{config['max_risk_discuss_rounds']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

