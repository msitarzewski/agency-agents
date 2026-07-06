"""
测试预估总时长修复
验证 RedisProgressTracker 初始化时是否正确设置 estimated_total_time
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.progress.tracker import RedisProgressTracker
import time

def test_estimated_total_time():
    """测试预估总时长"""
    print("=" * 70)
    print("测试预估总时长修复")
    print("=" * 70)
    
    # 测试场景1: 4级深度 + 3个分析师 + dashscope
    print("\n📊 测试场景1: 4级深度 + 3个分析师 + dashscope")
    print("-" * 70)
    
    tracker = RedisProgressTracker(
        task_id="test_task_1",
        analysts=["市场分析师", "新闻分析师", "基本面分析师"],
        research_depth="深度",
        llm_provider="dashscope"
    )
    
    # 获取进度数据
    progress = tracker.to_dict()
    
    print(f"✅ 任务ID: {progress['task_id']}")
    print(f"✅ 分析师数量: {len(progress['analysts'])}")
    print(f"✅ 研究深度: {progress['research_depth']}")
    print(f"✅ LLM提供商: {progress['llm_provider']}")
    print(f"✅ 预估总时长: {progress.get('estimated_total_time', 0)} 秒 ({progress.get('estimated_total_time', 0) / 60:.1f} 分钟)")
    print(f"✅ 预计剩余时间: {progress.get('remaining_time', 0)} 秒 ({progress.get('remaining_time', 0) / 60:.1f} 分钟)")
    
    # 验证预估总时长
    expected_time = 330 * 2.0 * 1.0  # 4级深度 + 3个分析师 + dashscope
    actual_time = progress.get('estimated_total_time', 0)
    
    if abs(actual_time - expected_time) < 1:
        print(f"✅ 预估总时长正确: {actual_time} 秒 (预期: {expected_time} 秒)")
    else:
        print(f"❌ 预估总时长错误: {actual_time} 秒 (预期: {expected_time} 秒)")
        return False
    
    # 测试场景2: 1级快速 + 1个分析师 + deepseek
    print("\n📊 测试场景2: 1级快速 + 1个分析师 + deepseek")
    print("-" * 70)
    
    tracker2 = RedisProgressTracker(
        task_id="test_task_2",
        analysts=["市场分析师"],
        research_depth="快速",
        llm_provider="deepseek"
    )
    
    progress2 = tracker2.to_dict()
    
    print(f"✅ 任务ID: {progress2['task_id']}")
    print(f"✅ 分析师数量: {len(progress2['analysts'])}")
    print(f"✅ 研究深度: {progress2['research_depth']}")
    print(f"✅ LLM提供商: {progress2['llm_provider']}")
    print(f"✅ 预估总时长: {progress2.get('estimated_total_time', 0)} 秒 ({progress2.get('estimated_total_time', 0) / 60:.1f} 分钟)")
    print(f"✅ 预计剩余时间: {progress2.get('remaining_time', 0)} 秒 ({progress2.get('remaining_time', 0) / 60:.1f} 分钟)")
    
    # 验证预估总时长
    expected_time2 = 150 * 1.0 * 0.8  # 1级快速 + 1个分析师 + deepseek
    actual_time2 = progress2.get('estimated_total_time', 0)
    
    if abs(actual_time2 - expected_time2) < 1:
        print(f"✅ 预估总时长正确: {actual_time2} 秒 (预期: {expected_time2} 秒)")
    else:
        print(f"❌ 预估总时长错误: {actual_time2} 秒 (预期: {expected_time2} 秒)")
        return False
    
    # 测试场景3: 5级全面 + 4个分析师 + google
    print("\n📊 测试场景3: 5级全面 + 4个分析师 + google")
    print("-" * 70)
    
    tracker3 = RedisProgressTracker(
        task_id="test_task_3",
        analysts=["市场分析师", "新闻分析师", "基本面分析师", "社媒分析师"],
        research_depth="全面",
        llm_provider="google"
    )
    
    progress3 = tracker3.to_dict()
    
    print(f"✅ 任务ID: {progress3['task_id']}")
    print(f"✅ 分析师数量: {len(progress3['analysts'])}")
    print(f"✅ 研究深度: {progress3['research_depth']}")
    print(f"✅ LLM提供商: {progress3['llm_provider']}")
    print(f"✅ 预估总时长: {progress3.get('estimated_total_time', 0)} 秒 ({progress3.get('estimated_total_time', 0) / 60:.1f} 分钟)")
    print(f"✅ 预计剩余时间: {progress3.get('remaining_time', 0)} 秒 ({progress3.get('remaining_time', 0) / 60:.1f} 分钟)")
    
    # 验证预估总时长
    expected_time3 = 480 * 2.4 * 1.2  # 5级全面 + 4个分析师 + google
    actual_time3 = progress3.get('estimated_total_time', 0)
    
    if abs(actual_time3 - expected_time3) < 1:
        print(f"✅ 预估总时长正确: {actual_time3} 秒 (预期: {expected_time3} 秒)")
    else:
        print(f"❌ 预估总时长错误: {actual_time3} 秒 (预期: {expected_time3} 秒)")
        return False
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过！")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_estimated_total_time()
    sys.exit(0 if success else 1)

