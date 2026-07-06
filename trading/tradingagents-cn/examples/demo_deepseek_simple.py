#!/usr/bin/env python3
"""
简化的DeepSeek演示 - 避免所有复杂导入
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

class SimpleDeepSeekAdapter:
    """简化的DeepSeek适配器"""
    
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未找到DEEPSEEK_API_KEY")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def chat(self, message: str) -> str:
        """简单聊天"""
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": message}],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content

def demo_simple_chat():
    """演示简单对话"""
    print("\n🤖 演示DeepSeek简单对话...")
    
    try:
        adapter = SimpleDeepSeekAdapter()
        
        message = """
        请简要介绍股票投资的基本概念，包括：
        1. 什么是股票
        2. 股票投资的风险
        3. 基本的投资策略
        请用中文回答，控制在200字以内。
        """
        
        print("💭 正在生成回答...")
        response = adapter.chat(message)
        print(f"🎯 DeepSeek回答:\n{response}")
        
        return True
        
    except Exception as e:
        print(f"❌ 简单对话演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_stock_analysis():
    """演示股票分析"""
    print("\n📊 演示DeepSeek股票分析...")
    
    try:
        adapter = SimpleDeepSeekAdapter()
        
        query = """
        假设你是一个专业的股票分析师，请分析以下情况：
        
        公司A：
        - 市盈率：15倍
        - 营收增长率：20%
        - 负债率：30%
        - 行业：科技
        
        公司B：
        - 市盈率：25倍
        - 营收增长率：8%
        - 负债率：50%
        - 行业：传统制造
        
        请从投资价值角度比较这两家公司，并给出投资建议。
        """
        
        print("🧠 正在进行股票分析...")
        response = adapter.chat(query)
        print(f"📈 分析结果:\n{response}")
        
        return True
        
    except Exception as e:
        print(f"❌ 股票分析演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始DeepSeek演示...")
    
    # 检查API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 未找到DEEPSEEK_API_KEY环境变量")
        print("请在.env文件中配置DEEPSEEK_API_KEY")
        return
    
    print(f"✅ 找到API密钥: {api_key[:10]}...")
    
    # 运行演示
    demos = [
        ("简单对话", demo_simple_chat),
        ("股票分析", demo_stock_analysis)
    ]
    
    results = []
    for name, demo_func in demos:
        print(f"\n{'='*50}")
        print(f"🎯 运行演示: {name}")
        print(f"{'='*50}")
        
        success = demo_func()
        results.append((name, success))
        
        if success:
            print(f"✅ {name} 演示成功")
        else:
            print(f"❌ {name} 演示失败")
    
    # 总结
    print(f"\n{'='*50}")
    print(f"📊 演示总结")
    print(f"{'='*50}")
    
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name}: {status}")
    
    successful_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    if successful_count == total_count:
        print(f"\n🎉 所有演示都成功完成！({successful_count}/{total_count})")
    else:
        print(f"\n⚠️  部分演示失败 ({successful_count}/{total_count})")

if __name__ == "__main__":
    main()