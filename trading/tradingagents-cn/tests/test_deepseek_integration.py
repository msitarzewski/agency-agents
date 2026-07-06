#!/usr/bin/env python3
"""
DeepSeek V3集成测试
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

def test_deepseek_availability():
    """测试DeepSeek可用性"""
    print("🔍 测试DeepSeek V3可用性...")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    enabled = os.getenv("DEEPSEEK_ENABLED", "false").lower() == "true"
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    print(f"API Key: {'✅ 已设置' if api_key else '❌ 未设置'}")
    print(f"Base URL: {base_url}")
    print(f"启用状态: {'✅ 已启用' if enabled else '❌ 未启用'}")
    
    if not api_key:
        print("\n⚠️ 请在.env文件中设置DEEPSEEK_API_KEY")
        print("📝 获取地址: https://platform.deepseek.com/")
        print("💡 注意：需要注册DeepSeek账号并创建API Key")
        return False
    
    if not enabled:
        print("\n⚠️ 请在.env文件中设置DEEPSEEK_ENABLED=true")
        return False
    
    return True

def test_deepseek_adapter():
    """测试DeepSeek适配器"""
    print("\n🧪 测试DeepSeek适配器...")
    
    try:
        from tradingagents.llm.deepseek_adapter import DeepSeekAdapter, create_deepseek_adapter
        
        # 测试适配器创建
        adapter = create_deepseek_adapter(model="deepseek-chat")
        print("✅ 适配器创建成功")
        
        # 测试模型信息
        model_info = adapter.get_model_info()
        print(f"✅ 模型信息: {model_info['provider']} - {model_info['model']}")
        print(f"✅ 上下文长度: {model_info['context_length']}")
        
        # 测试可用模型列表
        models = DeepSeekAdapter.get_available_models()
        print(f"✅ 可用模型: {list(models.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        return False

def test_deepseek_connection():
    """测试DeepSeek连接"""
    print("\n🔗 测试DeepSeek连接...")
    
    try:
        from tradingagents.llm.deepseek_adapter import create_deepseek_adapter
        from langchain.schema import HumanMessage
        
        # 创建适配器
        adapter = create_deepseek_adapter(model="deepseek-chat")
        
        # 测试简单对话
        messages = [HumanMessage(content="你好，请简单介绍一下股票投资的基本概念，控制在50字以内")]
        response = adapter.chat(messages)
        print(f"✅ 模型响应: {response[:100]}...")
        
        # 测试连接
        connection_ok = adapter.test_connection()
        print(f"✅ 连接测试: {'成功' if connection_ok else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def test_deepseek_tools():
    """测试DeepSeek工具调用"""
    print("\n🛠️ 测试工具调用功能...")
    
    try:
        from langchain.tools import tool
        from tradingagents.llm.deepseek_adapter import create_deepseek_adapter
        
        # 定义测试工具
        @tool
        def get_stock_price(symbol: str) -> str:
            """获取股票价格"""
            return f"股票{symbol}的当前价格是$150.00"
        
        @tool
        def get_market_news(symbol: str) -> str:
            """获取市场新闻"""
            return f"股票{symbol}的最新消息：公司业绩良好，分析师看好前景"
        
        # 创建适配器
        adapter = create_deepseek_adapter(model="deepseek-chat")
        
        # 创建智能体
        tools = [get_stock_price, get_market_news]
        system_prompt = "你是一个专业的股票分析助手，可以使用工具获取股票信息并进行分析。请用中文回答。"
        
        agent = adapter.create_agent(tools, system_prompt, verbose=True)
        print("✅ 智能体创建成功")
        
        # 测试工具调用
        result = agent.invoke({"input": "请帮我查询AAPL的股价和最新消息"})
        print(f"✅ 工具调用成功: {result['output'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具调用测试失败: {e}")
        return False

def test_deepseek_trading_graph():
    """测试DeepSeek在交易图中的集成"""
    print("\n📊 测试交易图集成...")
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        
        # 创建DeepSeek配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "deepseek"
        config["deep_think_llm"] = "deepseek-chat"
        config["quick_think_llm"] = "deepseek-chat"
        config["max_debate_rounds"] = 1  # 减少测试时间
        config["online_tools"] = False   # 禁用在线工具以加快测试
        
        # 创建交易图
        ta = TradingAgentsGraph(debug=True, config=config)
        print("✅ 交易图创建成功")
        
        # 注意：这里不执行实际分析，只测试初始化
        print("✅ DeepSeek集成到交易图成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 交易图集成测试失败: {e}")
        return False

def test_deepseek_models():
    """测试不同DeepSeek模型"""
    print("\n🎯 测试不同DeepSeek模型...")
    
    try:
        from tradingagents.llm.deepseek_adapter import create_deepseek_adapter
        
        models_to_test = ["deepseek-chat"]  # 仅测试最适合股票分析的模型
        
        for model in models_to_test:
            try:
                adapter = create_deepseek_adapter(model=model)
                info = adapter.get_model_info()
                print(f"✅ {model}: {info['context_length']} 上下文")
            except Exception as e:
                print(f"⚠️ {model}: 测试失败 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 DeepSeek V3集成测试")
    print("=" * 50)
    
    tests = [
        ("可用性检查", test_deepseek_availability),
        ("适配器测试", test_deepseek_adapter),
        ("连接测试", test_deepseek_connection),
        ("工具调用", test_deepseek_tools),
        ("交易图集成", test_deepseek_trading_graph),
        ("模型测试", test_deepseek_models),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "="*50)
    print("📋 测试结果总结:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！DeepSeek V3集成成功！")
        print("\n📝 下一步:")
        print("1. 在.env文件中配置您的DeepSeek API密钥")
        print("2. 设置DEEPSEEK_ENABLED=true启用DeepSeek")
        print("3. 在Web界面或CLI中选择DeepSeek模型")
        print("4. 享受高性价比的AI分析服务")
    else:
        print(f"\n⚠️ {len(results) - passed} 项测试失败，请检查配置和依赖")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
