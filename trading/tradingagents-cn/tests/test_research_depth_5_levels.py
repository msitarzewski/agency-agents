"""
测试5个研究深度级别的配置
"""
import pytest
from app.services.simple_analysis_service import create_analysis_config


class TestResearchDepth5Levels:
    """测试5个研究深度级别"""

    def test_depth_level_1_fast(self):
        """测试1级 - 快速分析"""
        config = create_analysis_config(
            research_depth="快速",
            selected_analysts=["market", "fundamentals"],
            quick_model="qwen-turbo",
            deep_model="qwen-plus",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 1
        assert config["memory_enabled"] is False  # 快速分析禁用记忆
        assert config["online_tools"] is False  # 快速分析禁用在线工具
        assert config["quick_think_llm"] == "qwen-turbo"
        assert config["deep_think_llm"] == "qwen-plus"

    def test_depth_level_2_basic(self):
        """测试2级 - 基础分析"""
        config = create_analysis_config(
            research_depth="基础",
            selected_analysts=["market", "fundamentals"],
            quick_model="qwen-turbo",
            deep_model="qwen-plus",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 1
        assert config["memory_enabled"] is True
        assert config["online_tools"] is True
        assert config["quick_think_llm"] == "qwen-turbo"
        assert config["deep_think_llm"] == "qwen-plus"

    def test_depth_level_3_standard(self):
        """测试3级 - 标准分析（推荐）"""
        config = create_analysis_config(
            research_depth="标准",
            selected_analysts=["market", "fundamentals"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 2  # 标准分析增加风险讨论
        assert config["memory_enabled"] is True
        assert config["online_tools"] is True
        assert config["quick_think_llm"] == "qwen-plus"
        assert config["deep_think_llm"] == "qwen-max"

    def test_depth_level_4_deep(self):
        """测试4级 - 深度分析"""
        config = create_analysis_config(
            research_depth="深度",
            selected_analysts=["market", "fundamentals"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 2  # 深度分析增加辩论轮次
        assert config["max_risk_discuss_rounds"] == 2
        assert config["memory_enabled"] is True
        assert config["online_tools"] is True
        assert config["quick_think_llm"] == "qwen-plus"
        assert config["deep_think_llm"] == "qwen-max"

    def test_depth_level_5_comprehensive(self):
        """测试5级 - 全面分析"""
        config = create_analysis_config(
            research_depth="全面",
            selected_analysts=["market", "fundamentals"],
            quick_model="qwen-max",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        assert config["max_debate_rounds"] == 3  # 全面分析最多辩论轮次
        assert config["max_risk_discuss_rounds"] == 3  # 全面分析最多风险讨论
        assert config["memory_enabled"] is True
        assert config["online_tools"] is True
        assert config["quick_think_llm"] == "qwen-max"
        assert config["deep_think_llm"] == "qwen-max"

    def test_unknown_depth_defaults_to_standard(self):
        """测试未知深度默认使用标准分析"""
        config = create_analysis_config(
            research_depth="未知级别",
            selected_analysts=["market", "fundamentals"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        
        # 应该使用标准分析的配置
        assert config["max_debate_rounds"] == 1
        assert config["max_risk_discuss_rounds"] == 2
        assert config["memory_enabled"] is True
        assert config["online_tools"] is True

    def test_all_depths_have_correct_progression(self):
        """测试所有深度级别的递进关系"""
        depths = ["快速", "基础", "标准", "深度", "全面"]
        configs = []
        
        for depth in depths:
            config = create_analysis_config(
                research_depth=depth,
                selected_analysts=["market", "fundamentals"],
                quick_model="qwen-plus",
                deep_model="qwen-max",
                llm_provider="dashscope",
                market_type="A股"
            )
            configs.append({
                "depth": depth,
                "debate_rounds": config["max_debate_rounds"],
                "risk_rounds": config["max_risk_discuss_rounds"],
                "memory": config["memory_enabled"],
                "online": config["online_tools"]
            })
        
        # 验证辩论轮次递增（除了前3级都是1轮）
        assert configs[0]["debate_rounds"] == 1  # 快速
        assert configs[1]["debate_rounds"] == 1  # 基础
        assert configs[2]["debate_rounds"] == 1  # 标准
        assert configs[3]["debate_rounds"] == 2  # 深度
        assert configs[4]["debate_rounds"] == 3  # 全面
        
        # 验证风险讨论轮次
        assert configs[0]["risk_rounds"] == 1  # 快速
        assert configs[1]["risk_rounds"] == 1  # 基础
        assert configs[2]["risk_rounds"] == 2  # 标准
        assert configs[3]["risk_rounds"] == 2  # 深度
        assert configs[4]["risk_rounds"] == 3  # 全面
        
        # 验证记忆和在线工具（快速分析禁用，其他启用）
        assert configs[0]["memory"] is False  # 快速
        assert configs[0]["online"] is False  # 快速
        for i in range(1, 5):
            assert configs[i]["memory"] is True
            assert configs[i]["online"] is True


class TestAnalysisParametersDefault:
    """测试分析参数的默认值"""

    def test_default_research_depth_is_standard(self):
        """测试默认研究深度是'标准'"""
        from app.models.analysis import AnalysisParameters
        
        params = AnalysisParameters()
        assert params.research_depth == "标准"

    def test_research_depth_accepts_all_5_levels(self):
        """测试研究深度接受所有5个级别"""
        from app.models.analysis import AnalysisParameters
        
        valid_depths = ["快速", "基础", "标准", "深度", "全面"]
        
        for depth in valid_depths:
            params = AnalysisParameters(research_depth=depth)
            assert params.research_depth == depth


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

