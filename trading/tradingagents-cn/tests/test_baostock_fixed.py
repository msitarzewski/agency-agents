#!/usr/bin/env python3
"""
测试修复后的BaoStock功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)

def test_baostock_query_all_stock_with_date():
    """测试带日期参数的query_all_stock"""
    print("=" * 60)
    print("🧪 测试带日期参数的BaoStock query_all_stock")
    print("=" * 60)
    
    try:
        import baostock as bs
        
        # 登录BaoStock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ BaoStock登录失败: {lg.error_msg}")
            return
        
        print("✅ BaoStock登录成功")
        
        # 测试不同的日期
        test_dates = [
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),  # 昨天
            (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),  # 前天
            "2024-12-31",  # 固定日期
        ]
        
        for test_date in test_dates:
            print(f"\n📅 测试日期: {test_date}")
            try:
                rs = bs.query_all_stock(day=test_date)
                print(f"   返回码: {rs.error_code}")
                print(f"   返回消息: {rs.error_msg}")
                
                if rs.error_code == '0':
                    # 解析数据
                    data_list = []
                    count = 0
                    while (rs.error_code == '0') & rs.next():
                        row = rs.get_row_data()
                        data_list.append(row)
                        count += 1
                        if count <= 5:  # 只显示前5条
                            print(f"     第{count}条: {row}")
                        if count >= 50:  # 限制总数
                            break
                    
                    print(f"   ✅ 获取到 {len(data_list)} 条记录")
                    
                    # 分析A股股票
                    a_stocks = [row for row in data_list if row[0].startswith(('sh.', 'sz.')) and len(row[0]) == 9]
                    print(f"   📊 A股股票数量: {len(a_stocks)}")
                    
                    if len(a_stocks) > 0:
                        print(f"   A股样本:")
                        for i, row in enumerate(a_stocks[:3]):
                            print(f"     {row[0]} - {row[2]}")
                        break  # 找到有效数据就退出
                else:
                    print(f"   ❌ 查询失败: {rs.error_msg}")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
        
        bs.logout()
        print("\n✅ BaoStock登出成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_baostock_adapter_fixed():
    """测试修复后的BaoStock适配器"""
    print("\n" + "=" * 60)
    print("🧪 测试修复后的BaoStock适配器")
    print("=" * 60)
    
    try:
        from app.services.data_source_adapters import BaoStockAdapter
        
        adapter = BaoStockAdapter()
        
        if not adapter.is_available():
            print("❌ BaoStock适配器不可用")
            return
        
        print("✅ BaoStock适配器可用")
        
        # 1. 测试股票列表获取
        print("\n1. 测试股票列表获取...")
        df = adapter.get_stock_list()
        
        if df is not None and not df.empty:
            print(f"✅ 股票列表获取成功: {len(df)}条记录")
            print(f"   列名: {list(df.columns)}")
            print(f"   前5条记录:")
            for i, row in df.head().iterrows():
                print(f"     {row.get('symbol', 'N/A')} - {row.get('name', 'N/A')} - {row.get('ts_code', 'N/A')}")
        else:
            print("❌ 股票列表获取失败")
            return
        
        # 2. 测试daily_basic获取
        print("\n2. 测试daily_basic数据获取...")
        trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print(f"   获取{trade_date}的数据...")
        
        basic_df = adapter.get_daily_basic(trade_date)
        
        if basic_df is not None and not basic_df.empty:
            print(f"✅ daily_basic数据获取成功: {len(basic_df)}条记录")
            print(f"   列名: {list(basic_df.columns)}")
            
            # 显示前几条记录
            print(f"   前5条记录:")
            for i, row in basic_df.head().iterrows():
                print(f"     {row.get('ts_code', 'N/A')} - {row.get('name', 'N/A')}")
                print(f"       PE: {row.get('pe', 'N/A')}, PB: {row.get('pb', 'N/A')}")
                print(f"       收盘价: {row.get('close', 'N/A')}")
            
            # 统计有效数据
            pe_count = basic_df['pe'].notna().sum() if 'pe' in basic_df.columns else 0
            pb_count = basic_df['pb'].notna().sum() if 'pb' in basic_df.columns else 0
            close_count = basic_df['close'].notna().sum() if 'close' in basic_df.columns else 0
            
            print(f"\n   📈 数据统计:")
            print(f"     有PE数据的股票: {pe_count}只")
            print(f"     有PB数据的股票: {pb_count}只")
            print(f"     有收盘价数据的股票: {close_count}只")
            
        else:
            print("❌ daily_basic数据获取失败")
        
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_data_source_manager_baostock():
    """测试数据源管理器中的BaoStock"""
    print("\n" + "=" * 60)
    print("🧪 测试数据源管理器中的BaoStock")
    print("=" * 60)
    
    try:
        from app.services.data_source_adapters import DataSourceManager
        
        manager = DataSourceManager()
        available_adapters = manager.get_available_adapters()
        
        print(f"✅ 可用数据源: {[adapter.name for adapter in available_adapters]}")
        
        # 查找BaoStock适配器
        baostock_adapter = None
        for adapter in available_adapters:
            if adapter.name == 'baostock':
                baostock_adapter = adapter
                break
        
        if baostock_adapter:
            print(f"✅ 找到BaoStock适配器，优先级: {baostock_adapter.priority}")
            
            # 测试股票列表获取
            print("\n📊 测试股票列表获取...")
            stock_df, source = manager.get_stock_list_with_fallback()
            
            if stock_df is not None and not stock_df.empty:
                print(f"✅ 股票列表获取成功: {len(stock_df)}条记录，来源: {source}")
                
                if source == 'baostock':
                    print(f"🎯 使用了BaoStock数据源!")
                else:
                    print(f"ℹ️ 使用了其他数据源: {source}")
            else:
                print(f"❌ 股票列表获取失败")
            
            # 测试daily_basic获取
            print("\n📊 测试daily_basic获取...")
            trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            
            basic_df, source = manager.get_daily_basic_with_fallback(trade_date)
            
            if basic_df is not None and not basic_df.empty:
                print(f"✅ daily_basic获取成功: {len(basic_df)}条记录，来源: {source}")
                
                if source == 'baostock':
                    print(f"🎯 使用了BaoStock数据源!")
                    # 检查BaoStock特有的估值指标
                    if 'ps' in basic_df.columns:
                        ps_count = basic_df['ps'].notna().sum()
                        print(f"   市销率(PS)数据: {ps_count}只股票")
                    if 'pcf' in basic_df.columns:
                        pcf_count = basic_df['pcf'].notna().sum()
                        print(f"   市现率(PCF)数据: {pcf_count}只股票")
                else:
                    print(f"ℹ️ 使用了其他数据源: {source}")
            else:
                print(f"❌ daily_basic获取失败")
        else:
            print(f"❌ 未找到BaoStock适配器")
        
    except Exception as e:
        print(f"❌ 数据源管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_baostock_query_all_stock_with_date()
    test_baostock_adapter_fixed()
    test_data_source_manager_baostock()
