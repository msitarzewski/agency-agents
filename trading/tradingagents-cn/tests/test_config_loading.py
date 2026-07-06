#!/usr/bin/env python3
"""
测试配置加载问题
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

def test_pricing_config_loading():
    """测试定价配置加载"""
    print("🔧 测试定价配置加载")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import ConfigManager
        
        # 创建配置管理器
        config_manager = ConfigManager()
        
        print(f"📁 配置目录: {config_manager.config_dir}")
        print(f"📄 定价文件: {config_manager.pricing_file}")
        print(f"📄 定价文件存在: {config_manager.pricing_file.exists()}")
        
        # 直接读取文件内容
        if config_manager.pricing_file.exists():
            with open(config_manager.pricing_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"📄 文件内容长度: {len(content)}")
            
            import json
            data = json.loads(content)
            print(f"📊 JSON中的配置数量: {len(data)}")
            
            for i, config in enumerate(data, 1):
                print(f"   {i}. {config['provider']}/{config['model_name']}")
        
        # 使用ConfigManager加载
        print(f"\n📊 使用ConfigManager加载:")
        pricing_configs = config_manager.load_pricing()
        print(f"📊 加载的配置数量: {len(pricing_configs)}")
        
        for i, config in enumerate(pricing_configs, 1):
            print(f"   {i}. {config.provider}/{config.model_name}")
        
        # 查找DeepSeek配置
        deepseek_configs = [p for p in pricing_configs if p.provider == "deepseek"]
        print(f"\n📊 DeepSeek配置数量: {len(deepseek_configs)}")
        
        # 查找百炼配置
        dashscope_configs = [p for p in pricing_configs if p.provider == "dashscope"]
        print(f"📊 百炼配置数量: {len(dashscope_configs)}")
        for config in dashscope_configs:
            print(f"   - {config.model_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cost_calculation():
    """测试成本计算"""
    print("\n💰 测试成本计算")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # 测试DeepSeek成本计算
        print("🤖 测试DeepSeek成本计算:")
        deepseek_cost = config_manager.calculate_cost(
            provider="deepseek",
            model_name="deepseek-chat",
            input_tokens=1000,
            output_tokens=500
        )
        print(f"   DeepSeek成本: ¥{deepseek_cost:.6f}")
        
        # 测试百炼成本计算
        print("🌟 测试百炼成本计算:")
        dashscope_cost1 = config_manager.calculate_cost(
            provider="dashscope",
            model_name="qwen-plus",
            input_tokens=1000,
            output_tokens=500
        )
        print(f"   qwen-plus成本: ¥{dashscope_cost1:.6f}")
        
        dashscope_cost2 = config_manager.calculate_cost(
            provider="dashscope",
            model_name="qwen-plus-latest",
            input_tokens=1000,
            output_tokens=500
        )
        print(f"   qwen-plus-latest成本: ¥{dashscope_cost2:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 成本计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 配置加载问题调试")
    print("=" * 80)
    
    # 测试配置加载
    loading_success = test_pricing_config_loading()
    
    # 测试成本计算
    calc_success = test_cost_calculation()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 60)
    
    print(f"配置加载: {'✅ 正常' if loading_success else '❌ 有问题'}")
    print(f"成本计算: {'✅ 正常' if calc_success else '❌ 有问题'}")
    
    overall_success = loading_success and calc_success
    
    if overall_success:
        print("\n🎉 配置系统正常工作！")
        print("   如果实际使用时仍有问题，可能是:")
        print("   1. 使用了不同的配置目录")
        print("   2. 配置被缓存了")
        print("   3. 模型名称在某个地方被修改了")
    else:
        print("\n❌ 配置系统有问题，需要修复")
    
    print("\n🎯 测试完成！")
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
