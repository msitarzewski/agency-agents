#!/usr/bin/env python3
"""
测试异步进度跟踪功能
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.utils.async_progress_tracker import AsyncProgressTracker, get_progress_by_id

def simulate_analysis(tracker: AsyncProgressTracker):
    """模拟分析过程"""
    print("🚀 开始模拟分析...")
    
    # 模拟分析过程 - 包含完整的步骤消息
    test_messages = [
        ("🚀 开始股票分析...", 1),                                    # 步骤1: 数据验证
        ("[进度] 🔍 验证股票代码并预获取数据...", 2),                    # 步骤1: 数据验证
        ("[进度] ✅ 数据准备完成: 五粮液 (A股)", 1),                    # 步骤1完成
        ("[进度] 检查环境变量配置...", 2),                             # 步骤2: 环境准备
        ("[进度] 环境变量验证通过", 1),                               # 步骤2完成
        ("[进度] 💰 预估分析成本: ¥0.0200", 2),                      # 步骤3: 成本预估
        ("[进度] 配置分析参数...", 1),                               # 步骤4: 参数配置
        ("[进度] 📁 创建必要的目录...", 1),                           # 步骤4继续
        ("[进度] 🔧 初始化分析引擎...", 2),                           # 步骤5: 引擎初始化
        ("[进度] 📊 开始分析 000858 股票，这可能需要几分钟时间...", 1),    # 步骤5完成
        ("📊 [模块开始] market_analyst - 股票: 000858", 3),          # 步骤6: 市场分析师
        ("📊 [市场分析师] 工具调用: ['get_stock_market_data_unified']", 15),
        ("📊 [模块完成] market_analyst - ✅ 成功 - 股票: 000858, 耗时: 41.73s", 2),
        ("📊 [模块开始] fundamentals_analyst - 股票: 000858", 3),    # 步骤7: 基本面分析师
        ("📊 [基本面分析师] 工具调用: ['get_stock_fundamentals_unified']", 20),
        ("📊 [模块完成] fundamentals_analyst - ✅ 成功 - 股票: 000858, 耗时: 35.21s", 2),
        ("📊 [模块开始] graph_signal_processing - 股票: 000858", 2), # 步骤8: 结果整理
        ("📊 [模块完成] graph_signal_processing - ✅ 成功 - 股票: 000858, 耗时: 2.20s", 1),
        ("✅ 分析完成", 1)                                          # 最终完成
    ]
    
    for i, (message, delay) in enumerate(test_messages):
        print(f"\n--- 步骤 {i+1} ---")
        print(f"📝 消息: {message}")
        
        tracker.update_progress(message)
        
        # 模拟处理时间
        time.sleep(delay)
    
    # 标记完成
    tracker.mark_completed("🎉 分析成功完成！")
    print("\n✅ 模拟分析完成")

def monitor_progress(analysis_id: str, max_duration: int = 120):
    """监控进度"""
    print(f"📊 开始监控进度: {analysis_id}")
    start_time = time.time()
    
    while time.time() - start_time < max_duration:
        progress_data = get_progress_by_id(analysis_id)
        
        if not progress_data:
            print("❌ 无法获取进度数据")
            break
        
        status = progress_data.get('status', 'running')
        current_step = progress_data.get('current_step', 0)
        total_steps = progress_data.get('total_steps', 8)
        progress_percentage = progress_data.get('progress_percentage', 0.0)
        step_name = progress_data.get('current_step_name', '未知')
        last_message = progress_data.get('last_message', '')
        elapsed_time = progress_data.get('elapsed_time', 0)
        remaining_time = progress_data.get('remaining_time', 0)
        
        print(f"\r📊 [{status}] 步骤 {current_step + 1}/{total_steps} ({progress_percentage:.1f}%) - {step_name} | "
              f"已用时: {elapsed_time:.1f}s, 剩余: {remaining_time:.1f}s | {last_message[:50]}...", end="")
        
        if status in ['completed', 'failed']:
            print(f"\n🎯 分析{status}: {last_message}")
            break
        
        time.sleep(1)
    
    print(f"\n📊 监控结束: {analysis_id}")

def test_async_progress():
    """测试异步进度跟踪"""
    print("🧪 测试异步进度跟踪...")
    
    # 创建跟踪器
    analysis_id = "test_analysis_12345"
    tracker = AsyncProgressTracker(
        analysis_id=analysis_id,
        analysts=['market', 'fundamentals'],
        research_depth=2,
        llm_provider='dashscope'
    )
    
    print(f"📊 创建跟踪器: {analysis_id}")
    print(f"⏱️ 预估总时长: {tracker.estimated_duration:.1f}秒")
    
    # 在后台线程运行分析模拟
    analysis_thread = threading.Thread(target=simulate_analysis, args=(tracker,))
    analysis_thread.daemon = True
    analysis_thread.start()
    
    # 在主线程监控进度
    monitor_progress(analysis_id)
    
    # 等待分析线程完成
    analysis_thread.join(timeout=10)
    
    # 最终状态
    final_progress = get_progress_by_id(analysis_id)
    if final_progress:
        print(f"\n🎯 最终状态:")
        print(f"   状态: {final_progress.get('status', 'unknown')}")
        print(f"   进度: {final_progress.get('progress_percentage', 0):.1f}%")
        print(f"   总耗时: {final_progress.get('elapsed_time', 0):.1f}秒")
        print(f"   最后消息: {final_progress.get('last_message', 'N/A')}")

if __name__ == "__main__":
    test_async_progress()
