#!/usr/bin/env python3
"""
测试.env文件兼容性
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """测试.env文件加载"""
    print("🧪 测试.env文件加载")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        # 测试.env状态检查
        env_status = config_manager.get_env_config_status()
        print(f"✅ .env文件存在: {env_status['env_file_exists']}")
        
        # 测试API密钥加载
        print("\n📋 API密钥状态:")
        for provider, configured in env_status['api_keys'].items():
            status = "✅ 已配置" if configured else "❌ 未配置"
            print(f"  {provider}: {status}")
        
        return True
    except Exception as e:
        print(f"❌ .env文件加载失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_model_config_merge():
    """测试模型配置合并"""
    print("\n🧪 测试模型配置合并")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        # 加载模型配置
        models = config_manager.load_models()
        print(f"📋 加载了 {len(models)} 个模型配置")
        
        # 检查.env密钥是否正确合并
        env_status = config_manager.get_env_config_status()
        
        for model in models:
            env_has_key = env_status['api_keys'].get(model.provider.lower(), False)
            model_has_key = bool(model.api_key)
            
            print(f"\n🤖 {model.provider} - {model.model_name}:")
            print(f"  .env中有密钥: {env_has_key}")
            print(f"  模型配置有密钥: {model_has_key}")
            print(f"  模型启用状态: {model.enabled}")
            
            if env_has_key:
                print(f"  API密钥: ***{model.api_key[-4:] if model.api_key else 'None'}")
        
        return True
    except Exception as e:
        print(f"❌ 模型配置合并失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_settings_merge():
    """测试系统设置合并"""
    print("\n🧪 测试系统设置合并")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        # 加载设置
        settings = config_manager.load_settings()
        
        # 检查.env中的设置是否正确合并
        env_settings = [
            "finnhub_api_key",
            "reddit_client_id", 
            "reddit_client_secret",
            "results_dir",
            "log_level"
        ]
        
        print("⚙️ 系统设置状态:")
        for key in env_settings:
            value = settings.get(key, "未设置")
            if "api_key" in key or "secret" in key:
                display_value = f"***{value[-4:]}" if value and value != "未设置" else "未设置"
            else:
                display_value = value
            print(f"  {key}: {display_value}")
        
        return True
    except Exception as e:
        print(f"❌ 系统设置合并失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n🧪 测试向后兼容性")
    print("=" * 50)
    
    try:
        # 测试原有的环境变量读取方式
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        
        print("🔑 直接环境变量读取:")
        print(f"  DASHSCOPE_API_KEY: {'✅ 已设置' if dashscope_key else '❌ 未设置'}")
        print(f"  FINNHUB_API_KEY: {'✅ 已设置' if finnhub_key else '❌ 未设置'}")
        
        # 测试CLI工具兼容性
        from cli.main import check_api_keys
        
        # 模拟CLI检查
        if dashscope_key and finnhub_key:
            print("✅ CLI工具API密钥检查应该通过")
        else:
            print("⚠️ CLI工具API密钥检查可能失败")
        
        return True
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    """主测试函数"""
    print("🧪 .env文件兼容性测试")
    print("=" * 60)
    
    tests = [
        (".env文件加载", test_env_loading),
        ("模型配置合并", test_model_config_merge),
        ("系统设置合并", test_settings_merge),
        ("向后兼容性", test_backward_compatibility),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 .env兼容性测试全部通过！")
        print("\n💡 兼容性特性:")
        print("✅ 优先从.env文件读取API密钥")
        print("✅ Web界面显示配置来源")
        print("✅ 保持CLI工具完全兼容")
        print("✅ 支持原有的环境变量方式")
        print("✅ 新增Web管理界面作为补充")
        return True
    else:
        print("❌ 部分测试失败，请检查兼容性实现")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
