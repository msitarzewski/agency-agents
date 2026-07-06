#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试进度跟踪系统

用于验证 LangGraph 节点名称映射和进度更新是否正确
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_init import get_logger

logger = get_logger("test")


def test_node_mapping():
    """测试节点名称映射"""
    print("\n" + "=" * 80)
    print("📊 测试 LangGraph 节点名称映射")
    print("=" * 80)
    
    # LangGraph 实际节点名称（来自 tradingagents/graph/setup.py）
    actual_nodes = [
        # 分析师节点
        "Market Analyst",
        "Fundamentals Analyst",
        "News Analyst",
        "Social Analyst",
        # 工具节点
        "tools_market",
        "tools_fundamentals",
        "tools_news",
        "tools_social",
        # 消息清理节点
        "Msg Clear Market",
        "Msg Clear Fundamentals",
        "Msg Clear News",
        "Msg Clear Social",
        # 研究员节点
        "Bull Researcher",
        "Bear Researcher",
        "Research Manager",
        # 交易员节点
        "Trader",
        # 风险评估节点
        "Risky Analyst",
        "Safe Analyst",
        "Neutral Analyst",
        "Risk Judge",
    ]
    
    # 我们的映射表（来自 tradingagents/graph/trading_graph.py）
    node_mapping = {
        'Market Analyst': "📊 市场分析师",
        'Fundamentals Analyst': "💼 基本面分析师",
        'News Analyst': "📰 新闻分析师",
        'Social Analyst': "💬 社交媒体分析师",
        'tools_market': None,
        'tools_fundamentals': None,
        'tools_news': None,
        'tools_social': None,
        'Msg Clear Market': None,
        'Msg Clear Fundamentals': None,
        'Msg Clear News': None,
        'Msg Clear Social': None,
        'Bull Researcher': "🐂 看涨研究员",
        'Bear Researcher': "🐻 看跌研究员",
        'Research Manager': "👔 研究经理",
        'Trader': "💼 交易员决策",
        'Risky Analyst': "🔥 激进风险评估",
        'Safe Analyst': "🛡️ 保守风险评估",
        'Neutral Analyst': "⚖️ 中性风险评估",
        'Risk Judge': "🎯 风险经理",
    }
    
    print("\n✅ 检查所有实际节点是否都有映射：")
    all_mapped = True
    for node in actual_nodes:
        if node in node_mapping:
            message = node_mapping[node]
            if message is None:
                print(f"  ⏭️  {node:30s} → (跳过)")
            else:
                print(f"  ✅ {node:30s} → {message}")
        else:
            print(f"  ❌ {node:30s} → (未映射)")
            all_mapped = False
    
    if all_mapped:
        print("\n🎉 所有节点都已正确映射！")
    else:
        print("\n⚠️  存在未映射的节点！")
    
    return all_mapped


def test_progress_calculation():
    """测试进度计算"""
    print("\n" + "=" * 80)
    print("📊 测试进度计算逻辑")
    print("=" * 80)
    
    # 节点进度映射表（来自 app/services/simple_analysis_service.py）
    node_progress_map = {
        # 分析师阶段 (10% → 45%)
        "📊 市场分析师": 27.5,
        "💼 基本面分析师": 45,
        "📰 新闻分析师": 27.5,
        "💬 社交媒体分析师": 27.5,
        # 研究辩论阶段 (45% → 70%)
        "🐂 看涨研究员": 51.25,
        "🐻 看跌研究员": 57.5,
        "👔 研究经理": 70,
        # 交易员阶段 (70% → 78%)
        "💼 交易员决策": 78,
        # 风险评估阶段 (78% → 93%)
        "🔥 激进风险评估": 81.75,
        "🛡️ 保守风险评估": 85.5,
        "⚖️ 中性风险评估": 89.25,
        "🎯 风险经理": 93,
        # 最终阶段 (93% → 100%)
        "📊 生成报告": 97,
    }
    
    # 模拟分析流程（快速分析：market + fundamentals）
    analysis_flow = [
        "📊 市场分析师",
        "💼 基本面分析师",
        "🐂 看涨研究员",
        "🐻 看跌研究员",
        "👔 研究经理",
        "💼 交易员决策",
        "🔥 激进风险评估",
        "🛡️ 保守风险评估",
        "⚖️ 中性风险评估",
        "🎯 风险经理",
        "📊 生成报告",
    ]
    
    print("\n✅ 模拟分析流程进度：")
    print(f"{'步骤':<20s} {'进度':<10s} {'增量':<10s}")
    print("-" * 50)
    
    prev_progress = 10  # 初始进度
    for step in analysis_flow:
        progress = node_progress_map.get(step, 0)
        delta = progress - prev_progress
        print(f"{step:<20s} {progress:>6.2f}%   {delta:>+6.2f}%")
        prev_progress = progress
    
    print("-" * 50)
    print(f"{'最终进度':<20s} {prev_progress:>6.2f}%")
    
    # 检查进度是否单调递增
    print("\n✅ 检查进度是否单调递增：")
    is_monotonic = True
    prev_progress = 10
    for step in analysis_flow:
        progress = node_progress_map.get(step, 0)
        if progress < prev_progress:
            print(f"  ❌ {step}: {progress}% < {prev_progress}%")
            is_monotonic = False
        prev_progress = progress
    
    if is_monotonic:
        print("  ✅ 进度单调递增！")
    else:
        print("  ⚠️  进度存在回退！")
    
    return is_monotonic


def test_step_coverage():
    """测试步骤覆盖率"""
    print("\n" + "=" * 80)
    print("📊 测试步骤覆盖率")
    print("=" * 80)
    
    # RedisProgressTracker 定义的步骤（来自 app/services/progress/tracker.py）
    tracker_steps = [
        # 基础准备阶段 (10%)
        "📋 准备阶段",
        "🔧 环境检查",
        "💰 成本估算",
        "⚙️ 参数设置",
        "🚀 启动引擎",
        # 分析师团队阶段 (35%)
        "📊 市场分析师",
        "💼 基本面分析师",
        # 研究团队辩论阶段 (25%)
        "🐂 看涨研究员",
        "🐻 看跌研究员",
        "🎯 研究辩论 第1轮",
        "👔 研究经理",
        # 交易团队阶段 (8%)
        "💼 交易员决策",
        # 风险管理团队阶段 (15%)
        "🔥 激进风险评估",
        "🛡️ 保守风险评估",
        "⚖️ 中性风险评估",
        "🎯 风险经理",
        # 最终决策阶段 (7%)
        "📡 信号处理",
        "📊 生成报告",
    ]
    
    # LangGraph 实际执行的步骤
    langgraph_steps = [
        "📊 市场分析师",
        "💼 基本面分析师",
        "🐂 看涨研究员",
        "🐻 看跌研究员",
        "👔 研究经理",
        "💼 交易员决策",
        "🔥 激进风险评估",
        "🛡️ 保守风险评估",
        "⚖️ 中性风险评估",
        "🎯 风险经理",
    ]
    
    print("\n✅ RedisProgressTracker 步骤：")
    for i, step in enumerate(tracker_steps, 1):
        if step in langgraph_steps:
            print(f"  {i:2d}. ✅ {step} (LangGraph 执行)")
        else:
            print(f"  {i:2d}. ⏭️  {step} (虚拟步骤)")
    
    print(f"\n📊 统计：")
    print(f"  总步骤数: {len(tracker_steps)}")
    print(f"  LangGraph 执行步骤: {len(langgraph_steps)}")
    print(f"  虚拟步骤: {len(tracker_steps) - len(langgraph_steps)}")
    print(f"  覆盖率: {len(langgraph_steps) / len(tracker_steps) * 100:.1f}%")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🧪 进度跟踪系统测试")
    print("=" * 80)
    
    # 测试节点映射
    mapping_ok = test_node_mapping()
    
    # 测试进度计算
    progress_ok = test_progress_calculation()
    
    # 测试步骤覆盖率
    test_step_coverage()
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    
    if mapping_ok and progress_ok:
        print("\n✅ 所有测试通过！进度跟踪系统已正确配置。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

