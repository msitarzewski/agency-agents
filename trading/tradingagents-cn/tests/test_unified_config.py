#!/usr/bin/env python3
"""
测试配置统一
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

def test_config_unification():
    """测试配置统一是否正常工作"""
    print("🔬 测试配置统一")
    print("=" * 60)
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        print("🔧 测试全局配置管理器...")
        
        # 检查配置目录
        print(f"📁 配置目录: {config_manager.config_dir}")
        print(f"📁 配置目录绝对路径: {config_manager.config_dir.absolute()}")
        print(f"📄 定价文件: {config_manager.pricing_file}")
        print(f"📄 定价文件存在: {config_manager.pricing_file.exists()}")
        
        # 加载定价配置
        pricing_configs = config_manager.load_pricing()
        print(f"📊 加载的定价配置数量: {len(pricing_configs)}")
        
        # 查找DeepSeek配置
        deepseek_configs = [p for p in pricing_configs if p.provider == "deepseek"]
        print(f"📊 DeepSeek配置数量: {len(deepseek_configs)}")
        
        if deepseek_configs:
            print("✅ 找到DeepSeek配置:")
            for config in deepseek_configs:
                print(f"   - {config.model_name}: 输入¥{config.input_price_per_1k}/1K, 输出¥{config.output_price_per_1k}/1K")
        else:
            print("❌ 未找到DeepSeek配置")
        
        # 测试成本计算
        print(f"\n💰 测试成本计算:")
        deepseek_cost = config_manager.calculate_cost(
            provider="deepseek",
            model_name="deepseek-chat",
            input_tokens=1000,
            output_tokens=500
        )
        print(f"   DeepSeek成本: ¥{deepseek_cost:.6f}")
        
        if deepseek_cost > 0:
            print("✅ DeepSeek成本计算正常")
            return True
        else:
            print("❌ DeepSeek成本计算仍为0")
            return False
        
    except Exception as e:
        print(f"❌ 配置统一测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_config_access():
    """测试Web界面配置访问"""
    print("\n🌐 测试Web界面配置访问")
    print("=" * 60)
    
    try:
        # 模拟Web界面的导入方式
        sys.path.insert(0, str(project_root / "web"))
        
        # 导入Web配置管理页面
        from pages.config_management import config_manager as web_config_manager
        
        print("🔧 测试Web配置管理器...")
        
        # 检查配置目录
        print(f"📁 Web配置目录: {web_config_manager.config_dir}")
        print(f"📁 Web配置目录绝对路径: {web_config_manager.config_dir.absolute()}")
        
        # 加载定价配置
        web_pricing_configs = web_config_manager.load_pricing()
        print(f"📊 Web加载的定价配置数量: {len(web_pricing_configs)}")
        
        # 查找DeepSeek配置
        web_deepseek_configs = [p for p in web_pricing_configs if p.provider == "deepseek"]
        print(f"📊 Web DeepSeek配置数量: {len(web_deepseek_configs)}")
        
        if web_deepseek_configs:
            print("✅ Web界面找到DeepSeek配置")
            return True
        else:
            print("❌ Web界面未找到DeepSeek配置")
            return False
        
    except Exception as e:
        print(f"❌ Web配置访问测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_consistency():
    """测试配置一致性"""
    print("\n🔄 测试配置一致性")
    print("=" * 60)
    
    try:
        from tradingagents.config.config_manager import config_manager
        
        # 从不同路径导入，应该使用相同的配置
        sys.path.insert(0, str(project_root / "web"))
        from pages.config_management import config_manager as web_config_manager
        
        # 比较配置目录
        main_config_dir = config_manager.config_dir.absolute()
        web_config_dir = web_config_manager.config_dir.absolute()
        
        print(f"📁 主配置目录: {main_config_dir}")
        print(f"📁 Web配置目录: {web_config_dir}")
        
        if main_config_dir == web_config_dir:
            print("✅ 配置目录一致")
            
            # 比较配置数量
            main_configs = config_manager.load_pricing()
            web_configs = web_config_manager.load_pricing()
            
            print(f"📊 主配置数量: {len(main_configs)}")
            print(f"📊 Web配置数量: {len(web_configs)}")
            
            if len(main_configs) == len(web_configs):
                print("✅ 配置数量一致")
                return True
            else:
                print("❌ 配置数量不一致")
                return False
        else:
            print("❌ 配置目录不一致")
            return False
        
    except Exception as e:
        print(f"❌ 配置一致性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 配置统一测试")
    print("=" * 80)
    print("📝 这个测试将验证配置统一是否成功")
    print("📝 检查所有组件是否使用相同的配置文件")
    print("=" * 80)
    
    # 测试配置统一
    unification_success = test_config_unification()
    
    # 测试Web配置访问
    web_access_success = test_web_config_access()
    
    # 测试配置一致性
    consistency_success = test_config_consistency()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 60)
    
    print(f"配置统一: {'✅ 成功' if unification_success else '❌ 失败'}")
    print(f"Web配置访问: {'✅ 成功' if web_access_success else '❌ 失败'}")
    print(f"配置一致性: {'✅ 成功' if consistency_success else '❌ 失败'}")
    
    overall_success = unification_success and web_access_success and consistency_success
    
    if overall_success:
        print("\n🎉 配置统一成功！")
        print("   现在所有组件都使用项目根目录的统一配置")
        print("   不再需要维护多套配置文件")
    else:
        print("\n❌ 配置统一失败")
        print("   需要进一步调试")
    
    print("\n🎯 测试完成！")
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
