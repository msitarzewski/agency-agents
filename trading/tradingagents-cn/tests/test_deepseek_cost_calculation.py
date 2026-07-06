#!/usr/bin/env python3
"""
测试DeepSeek成本计算修复
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

def test_deepseek_pricing_config():
    """测试DeepSeek定价配置"""
    print("🔧 测试DeepSeek定价配置")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import ConfigManager
        
        # 创建配置管理器
        config_manager = ConfigManager()
        
        # 加载定价配置
        pricing_configs = config_manager.load_pricing()
        
        print(f"📊 加载的定价配置数量: {len(pricing_configs)}")
        
        # 查找DeepSeek配置
        deepseek_configs = [p for p in pricing_configs if p.provider == "deepseek"]
        
        print(f"📊 DeepSeek定价配置数量: {len(deepseek_configs)}")
        
        for config in deepseek_configs:
            print(f"   模型: {config.model_name}")
            print(f"   输入价格: ¥{config.input_price_per_1k}/1K tokens")
            print(f"   输出价格: ¥{config.output_price_per_1k}/1K tokens")
            print(f"   货币: {config.currency}")
            print()
        
        return len(deepseek_configs) > 0
        
    except Exception as e:
        print(f"❌ 定价配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deepseek_cost_calculation():
    """测试DeepSeek成本计算"""
    print("💰 测试DeepSeek成本计算")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import ConfigManager
        
        # 创建配置管理器
        config_manager = ConfigManager()
        
        # 测试成本计算
        test_cases = [
            {"input_tokens": 1000, "output_tokens": 500},
            {"input_tokens": 2617, "output_tokens": 312},  # 实际使用的token数
            {"input_tokens": 3240, "output_tokens": 320},
            {"input_tokens": 1539, "output_tokens": 103},
        ]
        
        for i, case in enumerate(test_cases, 1):
            input_tokens = case["input_tokens"]
            output_tokens = case["output_tokens"]
            
            cost = config_manager.calculate_cost(
                provider="deepseek",
                model_name="deepseek-chat",
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            print(f"测试用例 {i}:")
            print(f"   输入tokens: {input_tokens}")
            print(f"   输出tokens: {output_tokens}")
            print(f"   计算成本: ¥{cost:.6f}")
            
            # 手动验证计算
            expected_cost = (input_tokens / 1000) * 0.0014 + (output_tokens / 1000) * 0.0028
            print(f"   预期成本: ¥{expected_cost:.6f}")
            print(f"   计算正确: {'✅' if abs(cost - expected_cost) < 0.000001 else '❌'}")
            print()
            
            if cost == 0.0:
                print(f"❌ 成本计算返回0，说明配置有问题")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 成本计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_tracker():
    """测试Token跟踪器"""
    print("📊 测试Token跟踪器")
    print("=" * 50)
    
    try:
        from tradingagents.config.config_manager import ConfigManager, TokenTracker
        
        # 创建配置管理器和Token跟踪器
        config_manager = ConfigManager()
        token_tracker = TokenTracker(config_manager)
        
        # 测试跟踪使用
        usage_record = token_tracker.track_usage(
            provider="deepseek",
            model_name="deepseek-chat",
            input_tokens=1000,
            output_tokens=500,
            session_id="test_session",
            analysis_type="test_analysis"
        )
        
        if usage_record:
            print(f"✅ Token跟踪成功")
            print(f"   提供商: {usage_record.provider}")
            print(f"   模型: {usage_record.model_name}")
            print(f"   输入tokens: {usage_record.input_tokens}")
            print(f"   输出tokens: {usage_record.output_tokens}")
            print(f"   成本: ¥{usage_record.cost:.6f}")
            print(f"   会话ID: {usage_record.session_id}")
            
            if usage_record.cost > 0:
                print(f"✅ 成本计算正确")
                return True
            else:
                print(f"❌ 成本计算仍为0")
                return False
        else:
            print(f"❌ Token跟踪失败")
            return False
        
    except Exception as e:
        print(f"❌ Token跟踪器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deepseek_adapter_integration():
    """测试DeepSeek适配器集成"""
    print("🤖 测试DeepSeek适配器集成")
    print("=" * 50)
    
    try:
        # 检查API密钥
        if not os.getenv("DEEPSEEK_API_KEY"):
            print("⚠️ 未找到DEEPSEEK_API_KEY，跳过适配器测试")
            return True
        
        from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
        
        # 创建DeepSeek实例
        deepseek_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=100
        )
        
        # 测试简单调用
        print("📤 发送测试请求...")
        result = deepseek_llm.invoke("请用一句话介绍DeepSeek")
        
        print(f"📊 响应类型: {type(result)}")
        print(f"📊 响应内容长度: {len(result.content)}")
        print(f"📊 响应内容: {result.content[:100]}...")
        
        # 检查是否有成本信息输出
        print(f"✅ DeepSeek适配器集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek适配器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 DeepSeek成本计算修复验证")
    print("=" * 80)
    
    # 测试定价配置
    config_success = test_deepseek_pricing_config()
    
    # 测试成本计算
    calc_success = test_deepseek_cost_calculation()
    
    # 测试Token跟踪器
    tracker_success = test_token_tracker()
    
    # 测试适配器集成
    adapter_success = test_deepseek_adapter_integration()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 60)
    
    print(f"定价配置: {'✅ 正确' if config_success else '❌ 有问题'}")
    print(f"成本计算: {'✅ 正确' if calc_success else '❌ 有问题'}")
    print(f"Token跟踪: {'✅ 正确' if tracker_success else '❌ 有问题'}")
    print(f"适配器集成: {'✅ 正确' if adapter_success else '❌ 有问题'}")
    
    overall_success = config_success and calc_success and tracker_success and adapter_success
    
    if overall_success:
        print("\n🎉 DeepSeek成本计算修复成功！")
        print("   - 定价配置已正确设置")
        print("   - 成本计算逻辑正常工作")
        print("   - Token跟踪器正确记录成本")
        print("   - 适配器集成正常")
        print("\n现在DeepSeek的token使用成本应该正确显示了！")
    else:
        print("\n⚠️ DeepSeek成本计算仍有问题")
        print("   请检查上述失败的测试项目")
    
    print("\n🎯 测试完成！")
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
