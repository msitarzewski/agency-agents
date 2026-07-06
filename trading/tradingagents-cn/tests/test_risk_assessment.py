#!/usr/bin/env python3
"""
测试风险评估功能
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

def test_risk_assessment_extraction():
    """测试风险评估数据提取功能"""
    print("🧪 测试风险评估数据提取")
    print("=" * 50)
    
    try:
        from web.utils.analysis_runner import extract_risk_assessment
        
        # 模拟分析状态数据
        mock_state = {
            'risk_debate_state': {
                'risky_history': """
作为激进风险分析师，我认为AAPL当前具有以下风险特征：

1. **市场机会**: 当前市场情绪积极，技术创新持续推进
2. **增长潜力**: 新产品线和服务业务增长强劲
3. **风险可控**: 虽然存在市场波动，但公司基本面稳健

建议: 适度增加仓位，把握成长机会
                """.strip(),
                
                'safe_history': """
作为保守风险分析师，我对AAPL持谨慎态度：

1. **市场风险**: 当前估值偏高，存在回调风险
2. **行业竞争**: 智能手机市场竞争激烈，增长放缓
3. **宏观环境**: 利率上升和经济不确定性增加风险

建议: 保持谨慎，控制仓位规模
                """.strip(),
                
                'neutral_history': """
作为中性风险分析师，我的综合评估如下：

1. **平衡视角**: AAPL既有增长机会也面临挑战
2. **风险收益**: 当前风险收益比处于合理区间
3. **时机选择**: 建议分批建仓，降低时机风险

建议: 采用均衡策略，适度配置
                """.strip(),
                
                'judge_decision': """
经过风险委员会充分讨论，对AAPL的风险评估结论如下：

**综合风险等级**: 中等风险
**主要风险因素**: 
- 估值风险: 当前P/E比率偏高
- 市场风险: 科技股波动性较大
- 竞争风险: 行业竞争加剧

**风险控制建议**:
1. 建议仓位控制在5-10%
2. 设置止损位在当前价格-15%
3. 分批建仓，降低时机风险
4. 密切关注季度财报和产品发布

**最终建议**: 谨慎乐观，适度配置
                """.strip()
            }
        }
        
        # 测试提取功能
        risk_assessment = extract_risk_assessment(mock_state)
        
        if risk_assessment:
            print("✅ 风险评估数据提取成功")
            print("\n📋 提取的风险评估报告:")
            print("-" * 50)
            print(risk_assessment[:500] + "..." if len(risk_assessment) > 500 else risk_assessment)
            print("-" * 50)
            
            # 验证报告内容
            required_sections = [
                "激进风险分析师观点",
                "中性风险分析师观点", 
                "保守风险分析师观点",
                "风险管理委员会最终决议"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in risk_assessment:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"⚠️ 缺少以下部分: {', '.join(missing_sections)}")
                return False
            else:
                print("✅ 风险评估报告包含所有必需部分")
                return True
        else:
            print("❌ 风险评估数据提取失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_web_interface_risk_display():
    """测试Web界面风险评估显示"""
    print("\n🧪 测试Web界面风险评估显示")
    print("=" * 50)
    
    try:
        from web.utils.analysis_runner import run_stock_analysis
        
        print("📋 检查Web界面分析运行器...")
        
        # 检查函数是否包含风险评估提取逻辑
        import inspect
        source = inspect.getsource(run_stock_analysis)
        
        if 'extract_risk_assessment' in source:
            print("✅ Web界面已集成风险评估提取功能")
        else:
            print("❌ Web界面缺少风险评估提取功能")
            return False
        
        if 'risk_assessment' in source:
            print("✅ Web界面支持风险评估数据传递")
        else:
            print("❌ Web界面缺少风险评估数据传递")
            return False
        
        print("✅ Web界面风险评估功能检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_risk_assessment_integration():
    """测试风险评估完整集成"""
    print("\n🧪 测试风险评估完整集成")
    print("=" * 50)
    
    try:
        # 检查API密钥
        dashscope_key = os.getenv('DASHSCOPE_API_KEY')
        google_key = os.getenv('GOOGLE_API_KEY')
        
        if not dashscope_key and not google_key:
            print("⚠️ 未配置API密钥，跳过实际分析测试")
            return True
        
        print("🚀 执行实际风险评估测试...")
        
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        if dashscope_key:
            config["llm_provider"] = "dashscope"
            config["deep_think_llm"] = "qwen-plus"
            config["quick_think_llm"] = "qwen-turbo"
        elif google_key:
            config["llm_provider"] = "google"
            config["deep_think_llm"] = "gemini-2.5-flash-lite-preview-06-17"
            config["quick_think_llm"] = "gemini-2.5-flash-lite-preview-06-17"
        
        config["online_tools"] = False  # 避免API限制
        config["memory_enabled"] = True
        config["max_risk_discuss_rounds"] = 1  # 减少测试时间
        
        # 修复路径
        config["data_dir"] = str(project_root / "data")
        config["results_dir"] = str(project_root / "results")
        config["data_cache_dir"] = str(project_root / "tradingagents" / "dataflows" / "data_cache")
        
        # 创建目录
        os.makedirs(config["data_dir"], exist_ok=True)
        os.makedirs(config["results_dir"], exist_ok=True)
        os.makedirs(config["data_cache_dir"], exist_ok=True)
        
        print("✅ 配置创建成功")
        
        # 创建TradingAgentsGraph实例
        print("🚀 初始化TradingAgents图...")
        graph = TradingAgentsGraph(["market", "fundamentals"], config=config, debug=False)
        
        print("✅ TradingAgents图初始化成功")
        
        # 执行分析
        print("📊 开始风险评估测试...")
        state, decision = graph.propagate("AAPL", "2025-06-27")
        
        # 检查风险评估数据
        if 'risk_debate_state' in state:
            print("✅ 发现风险评估数据")
            
            risk_debate = state['risk_debate_state']
            components = ['risky_history', 'safe_history', 'neutral_history', 'judge_decision']
            
            for component in components:
                if component in risk_debate and risk_debate[component]:
                    print(f"   ✅ {component}: 有数据")
                else:
                    print(f"   ❌ {component}: 无数据")
            
            # 测试提取功能
            from web.utils.analysis_runner import extract_risk_assessment
            risk_assessment = extract_risk_assessment(state)
            
            if risk_assessment:
                print("✅ 风险评估报告生成成功")
                print(f"   报告长度: {len(risk_assessment)} 字符")
                return True
            else:
                print("❌ 风险评估报告生成失败")
                return False
        else:
            print("❌ 未发现风险评估数据")
            return False
            
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    print("🧪 风险评估功能测试")
    print("=" * 70)
    
    # 运行测试
    results = {}
    
    results['数据提取'] = test_risk_assessment_extraction()
    results['Web界面集成'] = test_web_interface_risk_display()
    results['完整集成'] = test_risk_assessment_integration()
    
    # 总结结果
    print(f"\n📊 测试结果总结:")
    print("=" * 50)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    successful_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过")
    
    if successful_tests == total_tests:
        print("🎉 风险评估功能完全正常！")
        print("\n💡 现在Web界面应该能正确显示风险评估数据")
    else:
        print("⚠️ 部分功能需要进一步检查")

if __name__ == "__main__":
    main()
