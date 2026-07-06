#!/usr/bin/env python3
"""
简单基本面分析测试
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_simple_fundamentals():
    """测试简单的基本面分析流程"""
    print("\n🔍 简单基本面分析测试")
    print("=" * 80)
    
    # 测试分众传媒 002027
    test_ticker = "002027"
    print(f"📊 测试股票代码: {test_ticker} (分众传媒)")
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger = get_logger("default")
        logger.setLevel("INFO")
        
        print(f"\n🔧 步骤1: 创建LLM实例...")
        
        # 检查API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("⚠️ 未找到DASHSCOPE_API_KEY，跳过LLM测试")
            return True
        
        # 创建LLM实例
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        llm = ChatDashScopeOpenAI(
            model="qwen-turbo",
            temperature=0.1,
            max_tokens=1000
        )
        print(f"✅ LLM实例创建完成: {type(llm).__name__}")
        
        print(f"\n🔧 步骤2: 创建工具包...")
        
        # 创建工具包
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit()
        toolkit.update_config(config)
        print(f"✅ 工具包创建完成")
        
        print(f"\n🔧 步骤3: 测试统一基本面工具...")
        
        # 直接测试统一基本面工具
        result = toolkit.get_stock_fundamentals_unified.invoke({
            'ticker': test_ticker,
            'start_date': '2025-06-01',
            'end_date': '2025-07-15',
            'curr_date': '2025-07-15'
        })
        
        print(f"✅ 统一基本面工具调用完成")
        print(f"📊 返回结果长度: {len(result) if result else 0}")
        
        # 检查结果中的股票代码
        if result:
            print(f"\n🔍 检查工具返回结果中的股票代码...")
            if "002027" in result:
                print("✅ 工具返回结果中包含正确的股票代码 002027")
                count_002027 = result.count("002027")
                print(f"   002027 出现次数: {count_002027}")
            else:
                print("❌ 工具返回结果中不包含正确的股票代码 002027")
                
            if "002021" in result:
                print("⚠️ 工具返回结果中包含错误的股票代码 002021")
                count_002021 = result.count("002021")
                print(f"   002021 出现次数: {count_002021}")
            else:
                print("✅ 工具返回结果中不包含错误的股票代码 002021")
        
        print(f"\n🔧 步骤4: 测试LLM处理...")
        
        # 创建一个简单的提示词，包含工具返回的数据
        prompt = f"""请基于以下真实数据，对股票{test_ticker}进行基本面分析：

{result}

要求：
1. 分析要详细且专业
2. 必须使用中文
3. 股票代码必须准确
4. 不要编造任何信息
"""
        
        print(f"🔍 [股票代码追踪] 发送给LLM的提示词中的股票代码: {test_ticker}")
        
        # 调用LLM
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        
        print(f"✅ LLM调用完成")
        print(f"📊 LLM响应长度: {len(response.content) if response.content else 0}")
        
        # 检查LLM响应中的股票代码
        if response.content:
            print(f"\n🔍 检查LLM响应中的股票代码...")
            if "002027" in response.content:
                print("✅ LLM响应中包含正确的股票代码 002027")
                count_002027 = response.content.count("002027")
                print(f"   002027 出现次数: {count_002027}")
            else:
                print("❌ LLM响应中不包含正确的股票代码 002027")
                
            if "002021" in response.content:
                print("⚠️ LLM响应中包含错误的股票代码 002021")
                count_002021 = response.content.count("002021")
                print(f"   002021 出现次数: {count_002021}")
                
                # 找出错误代码的位置
                import re
                positions = [m.start() for m in re.finditer("002021", response.content)]
                print(f"   002021 出现位置: {positions}")
                
                # 显示错误代码周围的文本
                for pos in positions[:3]:  # 只显示前3个位置
                    start = max(0, pos - 100)
                    end = min(len(response.content), pos + 100)
                    context = response.content[start:end]
                    print(f"   位置 {pos} 周围文本: ...{context}...")
            else:
                print("✅ LLM响应中不包含错误的股票代码 002021")
                
            # 显示LLM响应的前1000字符
            print(f"\n📄 LLM响应前1000字符:")
            print("-" * 80)
            print(response.content[:1000])
            print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始简单基本面分析测试")
    
    # 执行测试
    success = test_simple_fundamentals()
    
    if success:
        print("\n✅ 测试完成")
    else:
        print("\n❌ 测试失败")
