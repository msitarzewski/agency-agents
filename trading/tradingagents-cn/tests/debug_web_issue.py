"""
调试Web界面显示"True"的问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_form_data_structure():
    """测试表单数据结构"""
    print("🧪 测试表单数据结构...")
    
    try:
        # 模拟表单数据
        form_data_submitted = {
            'submitted': True,
            'stock_symbol': '0700.HK',
            'market_type': '港股',
            'analysis_date': '2025-07-14',
            'analysts': ['market', 'fundamentals'],
            'research_depth': 3,
            'include_sentiment': True,
            'include_risk_assessment': True,
            'custom_prompt': ''
        }
        
        form_data_not_submitted = {
            'submitted': False
        }
        
        print("  提交时的表单数据:")
        for key, value in form_data_submitted.items():
            print(f"    {key}: {value} ({type(value).__name__})")
        
        print("\n  未提交时的表单数据:")
        for key, value in form_data_not_submitted.items():
            print(f"    {key}: {value} ({type(value).__name__})")
        
        # 检查条件判断
        if form_data_submitted.get('submitted', False):
            print("\n  ✅ 提交条件判断正确")
        else:
            print("\n  ❌ 提交条件判断错误")
        
        if form_data_not_submitted.get('submitted', False):
            print("  ❌ 未提交条件判断错误")
        else:
            print("  ✅ 未提交条件判断正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 表单数据结构测试失败: {e}")
        return False

def test_validation_function():
    """测试验证函数"""
    print("\n🧪 测试验证函数...")
    
    try:
        from web.utils.analysis_runner import validate_analysis_params
        
        # 测试港股验证
        errors = validate_analysis_params(
            stock_symbol="0700.HK",
            analysis_date="2025-07-14",
            analysts=["market", "fundamentals"],
            research_depth=3,
            market_type="港股"
        )
        
        print(f"  港股验证结果: {errors}")
        
        if not errors:
            print("  ✅ 港股验证通过")
        else:
            print(f"  ❌ 港股验证失败: {errors}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 验证函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analysis_runner_import():
    """测试分析运行器导入"""
    print("\n🧪 测试分析运行器导入...")
    
    try:
        from web.utils.analysis_runner import run_stock_analysis, validate_analysis_params, format_analysis_results
        print("  ✅ 分析运行器导入成功")
        
        # 测试函数签名
        import inspect
        
        sig = inspect.signature(run_stock_analysis)
        print(f"  run_stock_analysis 参数: {list(sig.parameters.keys())}")
        
        sig = inspect.signature(validate_analysis_params)
        print(f"  validate_analysis_params 参数: {list(sig.parameters.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析运行器导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_components():
    """测试Streamlit组件"""
    print("\n🧪 测试Streamlit组件...")
    
    try:
        # 测试组件导入
        from web.components.analysis_form import render_analysis_form
        from web.components.results_display import render_results
        
        print("  ✅ Streamlit组件导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_potential_output_sources():
    """检查可能的输出源"""
    print("\n🧪 检查可能的输出源...")
    
    # 检查可能输出"True"的地方
    potential_sources = [
        "表单提交状态直接输出",
        "布尔值转换为字符串",
        "调试语句残留",
        "异常处理中的输出",
        "Streamlit组件的意外输出"
    ]
    
    for source in potential_sources:
        print(f"  🔍 检查: {source}")
    
    print("\n  💡 建议检查:")
    print("    1. 搜索代码中的 st.write(True) 或类似语句")
    print("    2. 检查是否有 print(True) 语句")
    print("    3. 查看是否有布尔值被意外显示")
    print("    4. 检查表单组件的返回值处理")
    
    return True

def main():
    """运行所有调试测试"""
    print("🐛 开始调试Web界面'True'显示问题")
    print("=" * 50)
    
    tests = [
        test_form_data_structure,
        test_validation_function,
        test_analysis_runner_import,
        test_streamlit_components,
        check_potential_output_sources
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🐛 调试测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有测试通过，问题可能在Streamlit运行时环境")
    else:
        print("⚠️ 发现问题，请检查失败的测试项")
    
    print("\n🔧 解决建议:")
    print("1. 重启Streamlit应用")
    print("2. 清除浏览器缓存")
    print("3. 检查是否有残留的调试输出")
    print("4. 确认所有组件正确导入")

if __name__ == "__main__":
    main()
