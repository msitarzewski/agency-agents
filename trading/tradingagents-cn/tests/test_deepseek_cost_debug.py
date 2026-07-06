#!/usr/bin/env python3
"""
测试DeepSeek成本计算详细调试
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

def test_deepseek_cost_debug():
    """测试DeepSeek成本计算，观察详细日志"""
    print("🔬 DeepSeek成本计算详细调试")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 未找到DEEPSEEK_API_KEY，无法测试")
        return False
    
    try:
        from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
        
        print("🔧 创建DeepSeek实例...")
        
        # 创建DeepSeek实例
        deepseek_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=50  # 限制token数量，减少输出
        )
        
        print(f"📊 模型名称: {deepseek_llm.model_name}")
        print("\n" + "="*80)
        print("开始调用DeepSeek，观察详细的成本计算日志：")
        print("="*80)
        
        # 测试调用
        result = deepseek_llm.invoke("你好")
        
        print("="*80)
        print("调用完成！")
        print("="*80)
        
        print(f"📊 响应内容: {result.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 DeepSeek成本计算详细调试测试")
    print("=" * 80)
    print("📝 这个测试将显示成本计算的每个步骤")
    print("=" * 80)
    
    success = test_deepseek_cost_debug()
    
    if success:
        print("\n🎉 测试完成！")
        print("请查看上面的详细日志，找出成本计算为0的原因。")
    else:
        print("\n❌ 测试失败")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
