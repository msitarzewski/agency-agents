#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的深度级别验证脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit

def test_depth_level(depth):
    """测试指定深度级别"""
    print(f"\n{'='*50}")
    print(f"测试深度级别: {depth}")
    print(f"{'='*50}")
    
    # 设置研究深度
    Toolkit._config['research_depth'] = depth
    
    # 调用基本面分析
    result = Toolkit.get_stock_fundamentals_unified.invoke({
        'ticker': '300750',
        'start_date': "2024-10-10",
        'end_date': "2024-10-11",
        'curr_date': "2024-10-11"
    })
    
    # 分析结果
    lines = result.split('\n')
    char_count = len(result)
    
    # 查找数据深度级别
    depth_level = "未知"
    for line in lines:
        if "数据深度级别" in line:
            depth_level = line.split(":")[-1].strip()
            break
    
    print(f"📊 结果统计:")
    print(f"   - 数据深度级别: {depth_level}")
    print(f"   - 总行数: {len(lines)}")
    print(f"   - 总字符数: {char_count}")
    
    # 显示前几行内容
    print(f"\n📝 前10行内容:")
    for i, line in enumerate(lines[:10]):
        if line.strip():
            print(f"   {i+1}: {line[:100]}...")
    
    return {
        'depth_level': depth_level,
        'lines': len(lines),
        'chars': char_count,
        'content': result[:500] + "..." if len(result) > 500 else result
    }

def main():
    """主函数"""
    print("🔍 简单深度级别验证测试")
    
    # 保存原始配置
    original_depth = Toolkit._config.get('research_depth', 3)
    
    results = {}
    
    try:
        # 测试不同深度级别
        for depth in [1, 3, 5]:
            results[depth] = test_depth_level(depth)
        
        # 比较结果
        print(f"\n{'='*60}")
        print("📊 结果对比")
        print(f"{'='*60}")
        
        for depth in [1, 3, 5]:
            result = results[depth]
            print(f"深度 {depth}: {result['depth_level']} | {result['lines']} 行 | {result['chars']} 字符")
        
        # 检查差异
        levels = [results[d]['depth_level'] for d in [1, 3, 5]]
        chars = [results[d]['chars'] for d in [1, 3, 5]]
        
        print(f"\n✅ 验证结果:")
        print(f"   - 深度级别是否不同: {len(set(levels)) > 1}")
        print(f"   - 字符数变化: {chars[0]} → {chars[1]} → {chars[2]}")
        print(f"   - 数据量增长倍数: {chars[2] / chars[0]:.1f}x")
        
    finally:
        # 恢复原始配置
        Toolkit._config['research_depth'] = original_depth
        print(f"\n🔧 已恢复原始配置: research_depth = {original_depth}")

if __name__ == "__main__":
    main()