#!/usr/bin/env python3
"""
基本面报告生成测试
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_fundamentals_generation():
    """测试基本面报告生成过程"""
    print("\n🔍 基本面报告生成测试")
    print("=" * 80)
    
    # 测试分众传媒 002027
    test_ticker = "002027"
    print(f"📊 测试股票代码: {test_ticker} (分众传媒)")
    
    try:
        # 设置日志级别
        from tradingagents.utils.logging_init import get_logger
        logger = get_logger("default")
        logger.setLevel("INFO")
        
        print(f"\n🔧 步骤1: 获取股票数据...")
        
        # 获取股票数据
        from tradingagents.dataflows.interface import get_china_stock_data_tushare
        stock_data = get_china_stock_data_tushare(test_ticker, "2025-07-01", "2025-07-15")
        
        print(f"✅ 股票数据获取完成，长度: {len(stock_data) if stock_data else 0}")
        print(f"📄 股票数据前200字符: {stock_data[:200] if stock_data else 'None'}")
        
        print(f"\n🔧 步骤2: 生成基本面报告...")
        
        # 生成基本面报告
        from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
        analyzer = OptimizedChinaDataProvider()
        
        fundamentals_report = analyzer._generate_fundamentals_report(test_ticker, stock_data)
        
        print(f"\n✅ 基本面报告生成完成")
        print(f"📊 报告长度: {len(fundamentals_report) if fundamentals_report else 0}")
        
        # 检查报告中的股票代码
        if fundamentals_report:
            print(f"\n🔍 检查报告中的股票代码...")
            if "002027" in fundamentals_report:
                print("✅ 报告中包含正确的股票代码 002027")
                # 统计出现次数
                count_002027 = fundamentals_report.count("002027")
                print(f"   002027 出现次数: {count_002027}")
            else:
                print("❌ 报告中不包含正确的股票代码 002027")
                
            if "002021" in fundamentals_report:
                print("⚠️ 报告中包含错误的股票代码 002021")
                # 统计出现次数
                count_002021 = fundamentals_report.count("002021")
                print(f"   002021 出现次数: {count_002021}")
                
                # 找出错误代码的位置
                import re
                positions = [m.start() for m in re.finditer("002021", fundamentals_report)]
                print(f"   002021 出现位置: {positions}")
                
                # 显示错误代码周围的文本
                for pos in positions[:3]:  # 只显示前3个位置
                    start = max(0, pos - 50)
                    end = min(len(fundamentals_report), pos + 50)
                    context = fundamentals_report[start:end]
                    print(f"   位置 {pos} 周围文本: ...{context}...")
            else:
                print("✅ 报告中不包含错误的股票代码 002021")
                
            # 显示报告的前1000字符
            print(f"\n📄 报告前1000字符:")
            print("-" * 80)
            print(fundamentals_report[:1000])
            print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_industry_info():
    """测试行业信息获取"""
    print("\n🔧 测试行业信息获取")
    print("=" * 80)
    
    test_ticker = "002027"
    
    try:
        from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
        analyzer = OptimizedChinaDataProvider()
        
        print(f"🔧 测试 _get_industry_info...")
        industry_info = analyzer._get_industry_info(test_ticker)
        print(f"📊 行业信息: {industry_info}")
        
        print(f"\n🔧 测试 _estimate_financial_metrics...")
        financial_metrics = analyzer._estimate_financial_metrics(test_ticker, "¥7.67")
        print(f"📊 财务指标: {financial_metrics}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始基本面报告生成测试")
    
    # 测试1: 行业信息获取
    success1 = test_industry_info()
    
    # 测试2: 完整基本面报告生成
    success2 = test_fundamentals_generation()
    
    if success1 and success2:
        print("\n✅ 所有测试通过")
    else:
        print("\n❌ 部分测试失败")
