#!/usr/bin/env python3
"""
清理测试AKShare数据源优先级修复
强制重新加载模块以避免缓存问题
"""

import os
import sys
import importlib

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def clean_import_test():
    """清理导入测试"""
    print("🧹 清理导入测试")
    print("=" * 60)
    
    try:
        # 清理可能的模块缓存
        modules_to_clean = [
            'tradingagents.dataflows.data_source_manager',
            'tradingagents.dataflows',
            'tradingagents'
        ]
        
        for module_name in modules_to_clean:
            if module_name in sys.modules:
                print(f"🗑️ 清理模块缓存: {module_name}")
                del sys.modules[module_name]
        
        # 重新导入
        from tradingagents.dataflows.data_source_manager import DataSourceManager, ChinaDataSource
        
        # 创建数据源管理器
        manager = DataSourceManager()
        
        print(f"📊 默认数据源: {manager.default_source.value}")
        print(f"📊 当前数据源: {manager.current_source.value}")
        print(f"📊 可用数据源: {[s.value for s in manager.available_sources]}")
        
        # 验证默认数据源是AKShare
        if manager.default_source == ChinaDataSource.AKSHARE:
            print("✅ 默认数据源正确设置为AKShare")
            return True
        else:
            print(f"❌ 默认数据源错误: 期望akshare，实际{manager.default_source.value}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_variable_directly():
    """直接测试环境变量"""
    print("\n🔧 直接测试环境变量")
    print("=" * 60)
    
    try:
        # 检查环境变量
        env_value = os.getenv('DEFAULT_CHINA_DATA_SOURCE')
        print(f"📊 环境变量 DEFAULT_CHINA_DATA_SOURCE: {env_value}")
        
        # 检查.env文件
        env_file_path = os.path.join(project_root, '.env')
        if os.path.exists(env_file_path):
            print(f"📄 .env文件存在: {env_file_path}")
            with open(env_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'DEFAULT_CHINA_DATA_SOURCE' in content:
                    for line in content.split('\n'):
                        if 'DEFAULT_CHINA_DATA_SOURCE' in line and not line.strip().startswith('#'):
                            print(f"📊 .env文件中的设置: {line.strip()}")
                            break
        else:
            print("📄 .env文件不存在")
        
        # 手动加载.env文件
        try:
            from dotenv import load_dotenv
            load_dotenv()
            env_value_after_load = os.getenv('DEFAULT_CHINA_DATA_SOURCE')
            print(f"📊 加载.env后的环境变量: {env_value_after_load}")
        except ImportError:
            print("⚠️ python-dotenv未安装，无法自动加载.env文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_env_setting():
    """手动设置环境变量测试"""
    print("\n🔧 手动设置环境变量测试")
    print("=" * 60)
    
    try:
        # 手动设置环境变量
        os.environ['DEFAULT_CHINA_DATA_SOURCE'] = 'akshare'
        print(f"📊 手动设置环境变量: DEFAULT_CHINA_DATA_SOURCE=akshare")
        
        # 清理模块缓存
        modules_to_clean = [
            'tradingagents.dataflows.data_source_manager',
        ]
        
        for module_name in modules_to_clean:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # 重新导入
        from tradingagents.dataflows.data_source_manager import DataSourceManager, ChinaDataSource
        
        manager = DataSourceManager()
        
        print(f"📊 默认数据源: {manager.default_source.value}")
        print(f"📊 当前数据源: {manager.current_source.value}")
        
        if manager.default_source == ChinaDataSource.AKSHARE:
            print("✅ 手动设置环境变量后，默认数据源正确为AKShare")
            return True
        else:
            print(f"❌ 手动设置环境变量后，默认数据源仍然错误: {manager.default_source.value}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_order():
    """测试备用数据源顺序"""
    print("\n🔧 测试备用数据源顺序")
    print("=" * 60)
    
    try:
        # 确保环境变量设置
        os.environ['DEFAULT_CHINA_DATA_SOURCE'] = 'akshare'
        
        # 清理并重新导入
        if 'tradingagents.dataflows.data_source_manager' in sys.modules:
            del sys.modules['tradingagents.dataflows.data_source_manager']
        
        from tradingagents.dataflows.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        
        # 检查源代码中的fallback_order
        import inspect
        source_code = inspect.getsource(manager._try_fallback_sources)
        
        print("📊 检查备用数据源顺序...")
        
        # 查找fallback_order定义
        lines = source_code.split('\n')
        in_fallback_order = False
        fallback_sources = []
        
        for line in lines:
            if 'fallback_order = [' in line:
                in_fallback_order = True
                continue
            elif in_fallback_order:
                if ']' in line:
                    break
                if 'ChinaDataSource.' in line:
                    source_name = line.strip().replace('ChinaDataSource.', '').replace(',', '')
                    fallback_sources.append(source_name)
        
        print(f"📊 备用数据源顺序: {fallback_sources}")
        
        if fallback_sources and fallback_sources[0] == 'AKSHARE':
            print("✅ 备用数据源顺序正确: AKShare排在第一位")
            return True
        else:
            print(f"❌ 备用数据源顺序错误: 期望AKSHARE在第一位，实际顺序: {fallback_sources}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 AKShare数据源优先级修复验证 (清理版)")
    print("=" * 80)
    
    tests = [
        ("环境变量检查", test_env_variable_directly),
        ("手动环境变量设置", test_manual_env_setting),
        ("清理导入测试", clean_import_test),
        ("备用数据源顺序", test_fallback_order),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试{test_name}异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "=" * 80)
    print("📊 测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！AKShare数据源优先级修复成功！")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
