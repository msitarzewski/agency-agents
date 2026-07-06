#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试环境变量配置

用于验证聚合渠道的环境变量是否正确配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()


def test_env_variables():
    """测试环境变量配置"""
    
    print("=" * 60)
    print("🔍 聚合渠道环境变量配置检查")
    print("=" * 60)
    print()
    
    # 定义需要检查的环境变量
    env_vars = {
        "AI302_API_KEY": {
            "name": "302.AI",
            "required": False,
            "description": "302.AI 聚合平台 API Key"
        },
        "OPENROUTER_API_KEY": {
            "name": "OpenRouter",
            "required": False,
            "description": "OpenRouter 聚合平台 API Key"
        },
        "ONEAPI_API_KEY": {
            "name": "One API",
            "required": False,
            "description": "One API 自部署实例 API Key"
        },
        "ONEAPI_BASE_URL": {
            "name": "One API Base URL",
            "required": False,
            "description": "One API 自部署实例 Base URL"
        },
        "NEWAPI_API_KEY": {
            "name": "New API",
            "required": False,
            "description": "New API 自部署实例 API Key"
        },
        "NEWAPI_BASE_URL": {
            "name": "New API Base URL",
            "required": False,
            "description": "New API 自部署实例 Base URL"
        }
    }
    
    configured_count = 0
    total_count = len([v for v in env_vars.values() if "API_KEY" in v["description"]])
    
    for env_var, config in env_vars.items():
        value = os.getenv(env_var)
        
        # 检查是否配置
        is_configured = bool(value and not value.startswith('your_'))
        
        if is_configured:
            if "API_KEY" in env_var:
                configured_count += 1
            
            # 隐藏敏感信息
            if "API_KEY" in env_var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            else:
                display_value = value
            
            print(f"✅ {config['name']}")
            print(f"   变量名: {env_var}")
            print(f"   值: {display_value}")
            print(f"   说明: {config['description']}")
        else:
            status = "⚠️" if config["required"] else "⏭️"
            print(f"{status} {config['name']}")
            print(f"   变量名: {env_var}")
            print(f"   状态: 未配置")
            print(f"   说明: {config['description']}")
        
        print()
    
    print("=" * 60)
    print(f"📊 配置统计: {configured_count}/{total_count} 个聚合渠道已配置")
    print("=" * 60)
    print()
    
    # 给出建议
    if configured_count == 0:
        print("💡 建议:")
        print("   1. 编辑 .env 文件")
        print("   2. 添加至少一个聚合渠道的 API Key")
        print("   3. 推荐配置 AI302_API_KEY（国内访问稳定）")
        print()
        print("   示例:")
        print("   AI302_API_KEY=sk-xxxxx")
        print()
    elif configured_count < total_count:
        print("💡 提示:")
        print(f"   已配置 {configured_count} 个聚合渠道")
        print("   可以根据需要配置更多聚合渠道")
        print()
    else:
        print("🎉 太棒了！所有聚合渠道都已配置")
        print()
    
    return configured_count > 0


def test_service_integration():
    """测试服务集成"""
    
    print("=" * 60)
    print("🧪 测试服务集成")
    print("=" * 60)
    print()
    
    try:
        from app.services.config_service import ConfigService
        
        service = ConfigService()
        
        # 测试环境变量读取
        print("测试环境变量读取...")
        
        test_providers = ["302ai", "openrouter", "oneapi", "newapi"]
        
        for provider in test_providers:
            api_key = service._get_env_api_key(provider)
            
            if api_key:
                display_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
                print(f"✅ {provider}: {display_key}")
            else:
                print(f"⏭️ {provider}: 未配置")
        
        print()
        print("✅ 服务集成测试通过")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 服务集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """主函数"""
    
    print()
    print("🚀 TradingAgents-CN 聚合渠道环境变量测试")
    print()
    
    # 测试环境变量
    env_ok = test_env_variables()
    
    # 测试服务集成
    service_ok = test_service_integration()
    
    # 总结
    print("=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    print()
    
    if env_ok and service_ok:
        print("✅ 所有测试通过")
        print()
        print("下一步:")
        print("1. 启动后端服务")
        print("2. 调用初始化聚合渠道 API")
        print("3. 验证聚合渠道是否自动启用")
        print()
        return 0
    elif env_ok:
        print("⚠️ 环境变量配置正常，但服务集成测试失败")
        print()
        print("可能原因:")
        print("1. 依赖包未安装")
        print("2. 数据库未启动")
        print("3. 配置文件有误")
        print()
        return 1
    else:
        print("⚠️ 未配置聚合渠道环境变量")
        print()
        print("这不是错误，但建议配置至少一个聚合渠道以简化使用")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

