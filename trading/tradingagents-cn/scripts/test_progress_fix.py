#!/usr/bin/env python3
"""
测试修复后的进度跟踪功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.utils.progress_tracker import SmartAnalysisProgressTracker

def test_progress_tracker():
    """测试进度跟踪器"""
    print("🧪 测试进度跟踪器...")
    
    # 创建跟踪器
    tracker = SmartAnalysisProgressTracker(
        analysts=['market', 'fundamentals'],
        research_depth=2,
        llm_provider='dashscope'
    )
    
    print(f"📊 初始状态: 步骤 {tracker.current_step + 1}/{len(tracker.analysis_steps)}")
    print(f"⏱️ 预估总时长: {tracker.format_time(tracker.estimated_duration)}")
    
    # 模拟分析过程 - 包含完整的步骤消息
    test_messages = [
        "🚀 开始股票分析...",                                    # 步骤1: 数据验证
        "[进度] 🔍 验证股票代码并预获取数据...",                    # 步骤1: 数据验证
        "[进度] ✅ 数据准备完成: 五粮液 (A股)",                    # 步骤1完成
        "[进度] 检查环境变量配置...",                             # 步骤2: 环境准备
        "[进度] 环境变量验证通过",                               # 步骤2完成
        "[进度] 💰 预估分析成本: ¥0.0200",                      # 步骤3: 成本预估
        "[进度] 配置分析参数...",                               # 步骤4: 参数配置
        "[进度] 📁 创建必要的目录...",                           # 步骤4继续
        "[进度] 🔧 初始化分析引擎...",                           # 步骤5: 引擎初始化
        "[进度] 📊 开始分析 000858 股票，这可能需要几分钟时间...",    # 步骤5完成
        "📊 [模块开始] market_analyst - 股票: 000858",          # 步骤6: 市场分析师
        "📊 [市场分析师] 工具调用: ['get_stock_market_data_unified']",
        "📊 [模块完成] market_analyst - ✅ 成功 - 股票: 000858, 耗时: 41.73s",
        "📊 [模块开始] fundamentals_analyst - 股票: 000858",    # 步骤7: 基本面分析师
        "📊 [基本面分析师] 工具调用: ['get_stock_fundamentals_unified']",
        "📊 [模块完成] fundamentals_analyst - ✅ 成功 - 股票: 000858, 耗时: 35.21s",
        "📊 [模块开始] graph_signal_processing - 股票: 000858", # 步骤8: 结果整理
        "📊 [模块完成] graph_signal_processing - ✅ 成功 - 股票: 000858, 耗时: 2.20s",
        "✅ 分析完成"                                          # 最终完成
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n--- 消息 {i+1} ---")
        print(f"📝 消息: {message}")
        
        tracker.update(message)
        
        step_info = tracker.get_current_step_info()
        progress = tracker.get_progress_percentage()
        elapsed = tracker.get_elapsed_time()
        
        print(f"📊 当前步骤: {tracker.current_step + 1}/{len(tracker.analysis_steps)} - {step_info['name']}")
        print(f"📈 进度: {progress:.1f}%")
        print(f"⏱️ 已用时间: {tracker.format_time(elapsed)}")
        
        # 模拟时间间隔
        import time
        time.sleep(0.5)

if __name__ == "__main__":
    test_progress_tracker()
