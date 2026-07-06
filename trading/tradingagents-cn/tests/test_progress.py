#!/usr/bin/env python3
"""
测试进度显示功能
"""

import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_progress_callback():
    """测试进度回调功能"""
    
    def mock_progress_callback(message, step=None, total_steps=None):
        """模拟进度回调"""
        print(f"[进度] {message}")
        if step is not None and total_steps is not None:
            percentage = (step / total_steps) * 100
            print(f"  步骤: {step}/{total_steps} ({percentage:.1f}%)")
        print()
    
    # 模拟分析过程
    steps = [
        "开始股票分析...",
        "检查环境变量配置...",
        "环境变量验证通过",
        "配置分析参数...",
        "创建必要的目录...",
        "初始化分析引擎...",
        "开始分析 AAPL 股票，这可能需要几分钟时间...",
        "分析完成，正在整理结果...",
        "✅ 分析成功完成！"
    ]
    
    print("🧪 测试进度回调功能")
    print("=" * 50)
    
    for i, step in enumerate(steps):
        mock_progress_callback(step, i, len(steps))
        time.sleep(0.5)  # 模拟处理时间
    
    print("✅ 进度回调测试完成！")

def test_progress_tracker():
    """测试进度跟踪器"""
    try:
        from web.utils.progress_tracker import AnalysisProgressTracker
        
        print("🧪 测试进度跟踪器")
        print("=" * 50)
        
        def mock_callback(message, current_step, total_steps, progress, elapsed_time):
            print(f"[跟踪器] {message}")
            print(f"  步骤: {current_step + 1}/{total_steps}")
            print(f"  进度: {progress:.1%}")
            print(f"  用时: {elapsed_time:.1f}秒")
            print()
        
        tracker = AnalysisProgressTracker(callback=mock_callback)
        
        # 模拟分析步骤
        steps = [
            "开始股票分析...",
            "检查环境变量配置...",
            "配置分析参数...",
            "创建必要的目录...",
            "初始化分析引擎...",
            "获取股票数据...",
            "进行技术分析...",
            "分析完成，正在整理结果...",
            "✅ 分析成功完成！"
        ]
        
        for step in steps:
            tracker.update(step)
            time.sleep(0.3)
        
        print("✅ 进度跟踪器测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 进度跟踪器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 进度显示功能测试")
    print("=" * 60)
    
    # 测试基本进度回调
    test_progress_callback()
    print()
    
    # 测试进度跟踪器
    test_progress_tracker()
    
    print("\n🎉 所有测试完成！")

if __name__ == "__main__":
    main()
