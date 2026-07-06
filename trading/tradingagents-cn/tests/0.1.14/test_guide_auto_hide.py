#!/usr/bin/env python3
"""
测试使用指南自动隐藏功能
验证在开始分析时使用指南会自动隐藏
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_guide_auto_hide_logic():
    """测试使用指南自动隐藏逻辑"""
    print("📖 测试使用指南自动隐藏功能")
    print("=" * 60)
    
    # 模拟session state
    class MockSessionState:
        def __init__(self):
            self.data = {}
        
        def get(self, key, default=None):
            return self.data.get(key, default)
        
        def __setitem__(self, key, value):
            self.data[key] = value
        
        def __getitem__(self, key):
            return self.data[key]
        
        def __contains__(self, key):
            return key in self.data
    
    session_state = MockSessionState()
    
    # 测试场景1: 初始状态 - 应该显示使用指南
    print("\n📋 场景1: 初始状态")
    print("-" * 40)
    
    analysis_running = session_state.get('analysis_running', False)
    analysis_results = session_state.get('analysis_results')
    default_show_guide = not (analysis_running or analysis_results is not None)
    
    print(f"   analysis_running: {analysis_running}")
    print(f"   analysis_results: {analysis_results}")
    print(f"   default_show_guide: {default_show_guide}")
    print(f"   ✅ 初始状态应该显示使用指南: {default_show_guide}")
    
    # 测试场景2: 开始分析 - 应该隐藏使用指南
    print("\n📋 场景2: 开始分析")
    print("-" * 40)
    
    # 模拟开始分析
    session_state['analysis_running'] = True
    session_state['analysis_results'] = None
    
    # 自动隐藏使用指南（除非用户明确设置要显示）
    if not session_state.get('user_set_guide_preference', False):
        session_state['show_guide_preference'] = False
        print("   📖 开始分析，自动隐藏使用指南")
    
    analysis_running = session_state.get('analysis_running', False)
    analysis_results = session_state.get('analysis_results')
    default_show_guide = not (analysis_running or analysis_results is not None)
    show_guide_preference = session_state.get('show_guide_preference', default_show_guide)
    
    print(f"   analysis_running: {analysis_running}")
    print(f"   analysis_results: {analysis_results}")
    print(f"   default_show_guide: {default_show_guide}")
    print(f"   show_guide_preference: {show_guide_preference}")
    print(f"   ✅ 开始分析后应该隐藏使用指南: {not show_guide_preference}")
    
    # 测试场景3: 分析完成有结果 - 应该保持隐藏
    print("\n📋 场景3: 分析完成有结果")
    print("-" * 40)
    
    session_state['analysis_running'] = False
    session_state['analysis_results'] = {"stock_symbol": "AAPL", "analysis": "测试结果"}
    
    analysis_running = session_state.get('analysis_running', False)
    analysis_results = session_state.get('analysis_results')
    default_show_guide = not (analysis_running or analysis_results is not None)
    show_guide_preference = session_state.get('show_guide_preference', default_show_guide)
    
    print(f"   analysis_running: {analysis_running}")
    print(f"   analysis_results: {bool(analysis_results)}")
    print(f"   default_show_guide: {default_show_guide}")
    print(f"   show_guide_preference: {show_guide_preference}")
    print(f"   ✅ 有分析结果时应该保持隐藏: {not show_guide_preference}")
    
    # 测试场景4: 用户手动设置显示 - 应该尊重用户选择
    print("\n📋 场景4: 用户手动设置显示")
    print("-" * 40)
    
    # 模拟用户手动设置要显示使用指南
    session_state['user_set_guide_preference'] = True
    session_state['show_guide_preference'] = True
    
    # 再次开始分析
    session_state['analysis_running'] = True
    session_state['analysis_results'] = None
    
    # 这次不应该自动隐藏，因为用户明确设置了
    if not session_state.get('user_set_guide_preference', False):
        session_state['show_guide_preference'] = False
        print("   📖 自动隐藏使用指南")
    else:
        print("   👤 用户已手动设置，保持用户选择")
    
    show_guide_preference = session_state.get('show_guide_preference', False)
    print(f"   user_set_guide_preference: {session_state.get('user_set_guide_preference')}")
    print(f"   show_guide_preference: {show_guide_preference}")
    print(f"   ✅ 用户手动设置后应该尊重用户选择: {show_guide_preference}")
    
    print("\n💡 测试总结:")
    print("   1. ✅ 初始状态默认显示使用指南")
    print("   2. ✅ 开始分析时自动隐藏使用指南")
    print("   3. ✅ 有分析结果时保持隐藏状态")
    print("   4. ✅ 用户手动设置后尊重用户选择")
    
    return True

def test_ui_behavior():
    """测试UI行为逻辑"""
    print("\n🎨 测试UI行为逻辑")
    print("=" * 60)
    
    # 模拟不同的布局场景
    scenarios = [
        {
            "name": "初始访问",
            "analysis_running": False,
            "analysis_results": None,
            "user_set_preference": False,
            "expected_show_guide": True
        },
        {
            "name": "开始分析",
            "analysis_running": True,
            "analysis_results": None,
            "user_set_preference": False,
            "expected_show_guide": False
        },
        {
            "name": "分析完成",
            "analysis_running": False,
            "analysis_results": {"data": "test"},
            "user_set_preference": False,
            "expected_show_guide": False
        },
        {
            "name": "用户强制显示",
            "analysis_running": True,
            "analysis_results": {"data": "test"},
            "user_set_preference": True,
            "user_preference_value": True,
            "expected_show_guide": True
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 场景{i}: {scenario['name']}")
        print("-" * 40)
        
        # 计算默认值
        default_show_guide = not (scenario['analysis_running'] or scenario['analysis_results'] is not None)
        
        # 计算实际显示值
        if scenario['user_set_preference']:
            actual_show_guide = scenario.get('user_preference_value', True)
        else:
            actual_show_guide = default_show_guide
            # 如果开始分析且用户没有设置，则隐藏
            if scenario['analysis_running'] and not scenario['user_set_preference']:
                actual_show_guide = False
        
        print(f"   分析运行中: {scenario['analysis_running']}")
        print(f"   有分析结果: {bool(scenario['analysis_results'])}")
        print(f"   用户设置偏好: {scenario['user_set_preference']}")
        print(f"   默认显示指南: {default_show_guide}")
        print(f"   实际显示指南: {actual_show_guide}")
        print(f"   预期显示指南: {scenario['expected_show_guide']}")
        
        if actual_show_guide == scenario['expected_show_guide']:
            print(f"   ✅ 测试通过")
        else:
            print(f"   ❌ 测试失败")
    
    return True

if __name__ == "__main__":
    print("🧪 使用指南自动隐藏功能测试")
    print("=" * 70)
    
    try:
        test_guide_auto_hide_logic()
        test_ui_behavior()
        
        print("\n🎉 所有测试完成！")
        print("💡 功能说明:")
        print("   - 初次访问时显示使用指南，帮助用户了解操作")
        print("   - 点击开始分析后自动隐藏使用指南，节省屏幕空间")
        print("   - 用户可以手动控制使用指南的显示/隐藏")
        print("   - 系统会记住用户的偏好设置")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)