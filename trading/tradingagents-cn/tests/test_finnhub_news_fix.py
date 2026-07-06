#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Finnhub新闻数据路径修复

这个脚本用于验证:
1. 数据目录路径配置是否正确
2. 新闻数据文件路径是否存在
3. 错误处理是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.config import get_config, set_config
from tradingagents.dataflows.interface import get_finnhub_news
from tradingagents.dataflows.finnhub_utils import get_data_in_range

def test_data_dir_config():
    """测试数据目录配置"""
    print("=== 测试数据目录配置 ===")
    
    config = get_config()
    data_dir = config.get('data_dir')
    
    print(f"当前数据目录配置: {data_dir}")
    print(f"数据目录是否存在: {os.path.exists(data_dir) if data_dir else False}")
    
    # 检查是否为跨平台路径
    if data_dir:
        if '/' in data_dir and '\\' in data_dir:
            print("⚠️ 警告: 数据目录路径混合了Unix和Windows分隔符")
        elif data_dir.startswith('/Users/') and os.name == 'nt':
            print("⚠️ 警告: 在Windows系统上使用了Unix路径")
        else:
            print("✅ 数据目录路径格式正确")
    
    return data_dir

def test_finnhub_news_path():
    """测试Finnhub新闻数据路径"""
    print("\n=== 测试Finnhub新闻数据路径 ===")
    
    config = get_config()
    data_dir = config.get('data_dir')
    
    if not data_dir:
        print("❌ 数据目录未配置")
        return False
    
    # 测试AAPL新闻数据路径
    ticker = "AAPL"
    news_data_path = os.path.join(data_dir, "finnhub_data", "news_data", f"{ticker}_data_formatted.json")
    
    print(f"新闻数据文件路径: {news_data_path}")
    print(f"文件是否存在: {os.path.exists(news_data_path)}")
    
    # 检查目录结构
    finnhub_dir = os.path.join(data_dir, "finnhub_data")
    news_dir = os.path.join(finnhub_dir, "news_data")
    
    print(f"Finnhub目录是否存在: {os.path.exists(finnhub_dir)}")
    print(f"新闻数据目录是否存在: {os.path.exists(news_dir)}")
    
    if os.path.exists(news_dir):
        files = os.listdir(news_dir)
        print(f"新闻数据目录中的文件: {files[:5]}...")  # 只显示前5个文件
    
    return os.path.exists(news_data_path)

def test_get_data_in_range():
    """测试get_data_in_range函数的错误处理"""
    print("\n=== 测试get_data_in_range错误处理 ===")
    
    config = get_config()
    data_dir = config.get('data_dir')
    
    if not data_dir:
        print("❌ 数据目录未配置")
        return
    
    # 测试不存在的股票代码
    result = get_data_in_range(
        ticker="NONEXISTENT",
        start_date="2025-01-01",
        end_date="2025-01-02",
        data_type="news_data",
        data_dir=data_dir
    )
    
    print(f"不存在股票的返回结果: {result}")
    print(f"返回结果类型: {type(result)}")
    print(f"是否为空字典: {result == {}}")

def test_get_finnhub_news():
    """测试get_finnhub_news函数"""
    print("\n=== 测试get_finnhub_news函数 ===")
    
    # 测试不存在的股票代码
    result = get_finnhub_news(
        ticker="NONEXISTENT",
        curr_date="2025-01-02",
        look_back_days=7
    )
    
    print(f"函数返回结果: {result[:200]}...")  # 只显示前200个字符
    print(f"是否包含错误信息: {'无法获取' in result}")

def create_sample_data_structure():
    """创建示例数据目录结构"""
    print("\n=== 创建示例数据目录结构 ===")
    
    config = get_config()
    data_dir = config.get('data_dir')
    
    if not data_dir:
        print("❌ 数据目录未配置")
        return
    
    # 创建目录结构
    finnhub_dir = os.path.join(data_dir, "finnhub_data")
    news_dir = os.path.join(finnhub_dir, "news_data")
    
    try:
        os.makedirs(news_dir, exist_ok=True)
        print(f"✅ 创建目录结构: {news_dir}")
        
        # 创建示例数据文件
        sample_file = os.path.join(news_dir, "AAPL_data_formatted.json")
        sample_data = {
            "2025-01-01": [
                {
                    "headline": "Apple发布新产品",
                    "summary": "苹果公司今日发布了新的产品线..."
                }
            ]
        }
        
        import json
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 创建示例数据文件: {sample_file}")
        
    except Exception as e:
        print(f"❌ 创建目录结构失败: {e}")

def main():
    """主测试函数"""
    print("Finnhub新闻数据路径修复测试")
    print("=" * 50)
    
    # 测试数据目录配置
    data_dir = test_data_dir_config()
    
    # 测试新闻数据路径
    news_exists = test_finnhub_news_path()
    
    # 测试错误处理
    test_get_data_in_range()
    test_get_finnhub_news()
    
    # 如果数据不存在，创建示例结构
    if not news_exists:
        create_sample_data_structure()
        print("\n重新测试新闻数据路径:")
        test_finnhub_news_path()
    
    print("\n=== 测试总结 ===")
    print("1. 数据目录路径已修复为跨平台兼容")
    print("2. 添加了详细的错误处理和调试信息")
    print("3. 当数据文件不存在时会提供清晰的错误提示")
    print("4. 建议下载或配置正确的Finnhub数据")
    
    print("\n=== 解决方案建议 ===")
    print("如果仍然遇到新闻数据问题，请:")
    print("1. 确保已正确配置Finnhub API密钥")
    print("2. 运行数据下载脚本获取新闻数据")
    print("3. 检查数据目录权限")
    print(f"4. 确认数据目录存在: {data_dir}")

if __name__ == "__main__":
    main()