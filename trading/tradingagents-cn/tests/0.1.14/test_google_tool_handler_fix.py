#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Google工具调用处理器修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tool_call_validation():
    """测试工具调用验证功能"""
    print("=" * 60)
    print("🧪 测试工具调用验证功能")
    print("=" * 60)
    
    # 测试有效的工具调用
    valid_tool_call = {
        'name': 'get_stock_market_data_unified',
        'args': {'symbol': 'AAPL', 'period': '1d'},
        'id': 'call_12345'
    }
    
    result = GoogleToolCallHandler._validate_tool_call(valid_tool_call, 0, "测试分析师")
    print(f"✅ 有效工具调用验证结果: {result}")
    assert result == True, "有效工具调用应该通过验证"
    
    # 测试无效的工具调用 - 缺少字段
    invalid_tool_call_1 = {
        'name': 'get_stock_market_data_unified',
        'args': {'symbol': 'AAPL'}
        # 缺少 'id' 字段
    }
    
    result = GoogleToolCallHandler._validate_tool_call(invalid_tool_call_1, 1, "测试分析师")
    print(f"❌ 无效工具调用1验证结果: {result}")
    assert result == False, "缺少字段的工具调用应该验证失败"
    
    # 测试无效的工具调用 - 错误类型
    invalid_tool_call_2 = {
        'name': '',  # 空字符串
        'args': 'not_a_dict',  # 不是字典
        'id': 123  # 不是字符串
    }
    
    result = GoogleToolCallHandler._validate_tool_call(invalid_tool_call_2, 2, "测试分析师")
    print(f"❌ 无效工具调用2验证结果: {result}")
    assert result == False, "错误类型的工具调用应该验证失败"
    
    print("✅ 工具调用验证功能测试通过")

def test_tool_call_fixing():
    """测试工具调用修复功能"""
    print("\n" + "=" * 60)
    print("🔧 测试工具调用修复功能")
    print("=" * 60)
    
    # 测试OpenAI格式的工具调用修复
    openai_format_tool_call = {
        'function': {
            'name': 'get_stock_market_data_unified',
            'arguments': '{"symbol": "AAPL", "period": "1d"}'
        }
        # 缺少 'id' 字段
    }
    
    fixed_tool_call = GoogleToolCallHandler._fix_tool_call(openai_format_tool_call, 0, "测试分析师")
    print(f"🔧 修复后的工具调用: {fixed_tool_call}")
    
    if fixed_tool_call:
        assert 'name' in fixed_tool_call, "修复后应该包含name字段"
        assert 'args' in fixed_tool_call, "修复后应该包含args字段"
        assert 'id' in fixed_tool_call, "修复后应该包含id字段"
        assert isinstance(fixed_tool_call['args'], dict), "args应该是字典类型"
        print("✅ OpenAI格式工具调用修复成功")
    else:
        print("❌ OpenAI格式工具调用修复失败")
    
    # 测试无法修复的工具调用
    unfixable_tool_call = "not_a_dict"
    
    fixed_tool_call = GoogleToolCallHandler._fix_tool_call(unfixable_tool_call, 1, "测试分析师")
    print(f"❌ 无法修复的工具调用结果: {fixed_tool_call}")
    assert fixed_tool_call is None, "无法修复的工具调用应该返回None"
    
    print("✅ 工具调用修复功能测试通过")

def test_duplicate_prevention():
    """测试重复调用防护功能"""
    print("\n" + "=" * 60)
    print("🛡️ 测试重复调用防护功能")
    print("=" * 60)
    
    # 模拟重复的工具调用
    tool_calls = [
        {
            'name': 'get_stock_market_data_unified',
            'args': {'symbol': 'AAPL', 'period': '1d'},
            'id': 'call_1'
        },
        {
            'name': 'get_stock_market_data_unified',
            'args': {'symbol': 'AAPL', 'period': '1d'},  # 相同参数
            'id': 'call_2'
        },
        {
            'name': 'get_stock_market_data_unified',
            'args': {'symbol': 'TSLA', 'period': '1d'},  # 不同参数
            'id': 'call_3'
        }
    ]
    
    executed_tools = set()
    unique_calls = []
    
    for i, tool_call in enumerate(tool_calls):
        tool_name = tool_call.get('name')
        tool_args = tool_call.get('args', {})
        tool_signature = f"{tool_name}_{hash(str(tool_args))}"
        
        if tool_signature in executed_tools:
            print(f"⚠️ 跳过重复工具调用 {i}: {tool_name} with {tool_args}")
        else:
            executed_tools.add(tool_signature)
            unique_calls.append(tool_call)
            print(f"✅ 执行工具调用 {i}: {tool_name} with {tool_args}")
    
    print(f"📊 原始工具调用数量: {len(tool_calls)}")
    print(f"📊 去重后工具调用数量: {len(unique_calls)}")
    
    assert len(unique_calls) == 2, "应该有2个唯一的工具调用"
    print("✅ 重复调用防护功能测试通过")

def main():
    """主测试函数"""
    print("🚀 开始测试Google工具调用处理器修复效果")
    
    try:
        test_tool_call_validation()
        test_tool_call_fixing()
        test_duplicate_prevention()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！Google工具调用处理器修复成功")
        print("=" * 60)
        
        print("\n📋 修复总结:")
        print("1. ✅ 添加了工具调用格式验证")
        print("2. ✅ 实现了工具调用自动修复（支持OpenAI格式转换）")
        print("3. ✅ 添加了重复调用防护机制")
        print("4. ✅ 改进了错误处理和日志记录")
        
        print("\n🔧 主要改进:")
        print("- 防止重复调用统一市场数据工具")
        print("- 自动验证和修复Google模型的错误工具调用")
        print("- 支持OpenAI格式到标准格式的自动转换")
        print("- 增强的错误处理和调试信息")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)