#!/usr/bin/env python3
"""
诊断Tushare返回空数据的原因
分析时间参数、股票代码、API限制等可能的问题
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_time_parameters():
    """测试不同的时间参数"""
    print("🕐 测试时间参数...")
    print("=" * 60)
    
    # 测试不同的时间范围
    test_cases = [
        {
            "name": "原始问题时间",
            "start": "2025-01-10", 
            "end": "2025-01-17"
        },
        {
            "name": "最近7天",
            "start": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            "end": datetime.now().strftime('%Y-%m-%d')
        },
        {
            "name": "最近30天", 
            "start": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "end": datetime.now().strftime('%Y-%m-%d')
        },
        {
            "name": "2024年最后一周",
            "start": "2024-12-25",
            "end": "2024-12-31"
        },
        {
            "name": "2025年第一周",
            "start": "2025-01-01", 
            "end": "2025-01-07"
        }
    ]
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        provider = get_tushare_provider()
        
        if not provider.connected:
            print("❌ Tushare未连接")
            return
        
        symbol = "300033"  # 同花顺
        
        for case in test_cases:
            print(f"\n📅 {case['name']}: {case['start']} 到 {case['end']}")
            
            try:
                data = provider.get_stock_daily(symbol, case['start'], case['end'])
                
                if data is not None and not data.empty:
                    print(f"   ✅ 获取成功: {len(data)}条数据")
                    print(f"   📊 数据范围: {data['trade_date'].min()} 到 {data['trade_date'].max()}")
                else:
                    print(f"   ❌ 返回空数据")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
                
    except Exception as e:
        print(f"❌ 初始化失败: {e}")

def test_stock_codes():
    """测试不同的股票代码"""
    print("\n📊 测试不同股票代码...")
    print("=" * 60)
    
    # 测试不同类型的股票
    test_symbols = [
        {"code": "300033", "name": "同花顺", "market": "创业板"},
        {"code": "000001", "name": "平安银行", "market": "深圳主板"},
        {"code": "600036", "name": "招商银行", "market": "上海主板"},
        {"code": "688001", "name": "华兴源创", "market": "科创板"},
        {"code": "002415", "name": "海康威视", "market": "深圳中小板"},
    ]
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        provider = get_tushare_provider()
        
        if not provider.connected:
            print("❌ Tushare未连接")
            return
        
        # 使用最近7天的数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        print(f"📅 测试时间范围: {start_date} 到 {end_date}")
        
        for symbol_info in test_symbols:
            symbol = symbol_info["code"]
            print(f"\n📈 {symbol} ({symbol_info['name']} - {symbol_info['market']})")
            
            try:
                data = provider.get_stock_daily(symbol, start_date, end_date)
                
                if data is not None and not data.empty:
                    print(f"   ✅ 获取成功: {len(data)}条数据")
                    # 显示最新一条数据
                    latest = data.iloc[-1]
                    print(f"   💰 最新价格: {latest['close']:.2f}")
                else:
                    print(f"   ❌ 返回空数据")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
                
    except Exception as e:
        print(f"❌ 初始化失败: {e}")

def test_api_limits():
    """测试API限制和权限"""
    print("\n🔐 测试API限制和权限...")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        import time
        
        provider = get_tushare_provider()
        
        if not provider.connected:
            print("❌ Tushare未连接")
            return
        
        # 测试基本信息获取（通常权限要求较低）
        print("📋 测试股票基本信息获取...")
        try:
            stock_list = provider.get_stock_list()
            if stock_list is not None and not stock_list.empty:
                print(f"   ✅ 股票列表获取成功: {len(stock_list)}只股票")
            else:
                print(f"   ❌ 股票列表为空")
        except Exception as e:
            print(f"   ❌ 股票列表获取失败: {e}")
        
        # 测试连续调用（检查频率限制）
        print("\n⏱️ 测试API调用频率...")
        symbol = "000001"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        for i in range(3):
            print(f"   第{i+1}次调用...")
            start_time = time.time()
            
            try:
                data = provider.get_stock_daily(symbol, start_date, end_date)
                duration = time.time() - start_time
                
                if data is not None and not data.empty:
                    print(f"   ✅ 成功: {len(data)}条数据，耗时: {duration:.2f}秒")
                else:
                    print(f"   ❌ 空数据，耗时: {duration:.2f}秒")
                    
            except Exception as e:
                duration = time.time() - start_time
                print(f"   ❌ 异常: {e}，耗时: {duration:.2f}秒")
            
            # 短暂延迟避免频率限制
            if i < 2:
                time.sleep(1)
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_date_formats():
    """测试日期格式处理"""
    print("\n📅 测试日期格式处理...")
    print("=" * 60)
    
    # 测试不同的日期格式
    date_formats = [
        {"format": "YYYY-MM-DD", "start": "2025-01-10", "end": "2025-01-17"},
        {"format": "YYYYMMDD", "start": "20250110", "end": "20250117"},
    ]
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        provider = get_tushare_provider()
        
        if not provider.connected:
            print("❌ Tushare未连接")
            return
        
        symbol = "000001"
        
        for fmt in date_formats:
            print(f"\n📝 测试格式 {fmt['format']}: {fmt['start']} 到 {fmt['end']}")
            
            try:
                data = provider.get_stock_daily(symbol, fmt['start'], fmt['end'])
                
                if data is not None and not data.empty:
                    print(f"   ✅ 获取成功: {len(data)}条数据")
                else:
                    print(f"   ❌ 返回空数据")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    print("🔍 Tushare空数据问题诊断")
    print("=" * 80)
    
    # 1. 测试时间参数
    test_time_parameters()
    
    # 2. 测试股票代码
    test_stock_codes()
    
    # 3. 测试API限制
    test_api_limits()
    
    # 4. 测试日期格式
    test_date_formats()
    
    # 5. 总结
    print("\n📋 诊断总结")
    print("=" * 60)
    print("💡 可能的原因:")
    print("   1. 时间范围问题 - 查询的日期范围内没有交易数据")
    print("   2. 股票代码问题 - 股票代码格式不正确或股票已退市")
    print("   3. API权限问题 - Tushare账号权限不足")
    print("   4. 网络问题 - 网络连接不稳定")
    print("   5. 缓存问题 - 缓存了错误的空数据")
    print("   6. 交易日历 - 查询日期不是交易日")

if __name__ == "__main__":
    main()
