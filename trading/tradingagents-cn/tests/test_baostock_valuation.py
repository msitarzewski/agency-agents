#!/usr/bin/env python3
"""
测试BaoStock估值指标功能
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

def test_baostock_valuation_direct():
    """直接测试BaoStock估值指标API"""
    print("=" * 60)
    print("🧪 直接测试BaoStock估值指标API")
    print("=" * 60)
    
    try:
        import baostock as bs
        
        # 登录BaoStock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ BaoStock登录失败: {lg.error_msg}")
            return
        
        print("✅ BaoStock登录成功")
        
        # 测试股票代码
        test_codes = ['sh.600000', 'sz.000001', 'sh.600519']
        trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"📅 测试日期: {trade_date}")
        
        for code in test_codes:
            print(f"\n📊 测试股票: {code}")
            print("-" * 30)
            
            try:
                # 获取估值指标
                rs = bs.query_history_k_data_plus(
                    code,
                    "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM",
                    start_date=trade_date,
                    end_date=trade_date,
                    frequency="d",
                    adjustflag="3"
                )
                
                if rs.error_code == '0':
                    result_list = []
                    while (rs.error_code == '0') & rs.next():
                        result_list.append(rs.get_row_data())
                    
                    if result_list:
                        row = result_list[0]
                        print(f"✅ 估值数据获取成功:")
                        print(f"   日期: {row[0]}")
                        print(f"   代码: {row[1]}")
                        print(f"   收盘价: {row[2]}")
                        print(f"   滚动市盈率(peTTM): {row[3]}")
                        print(f"   市净率(pbMRQ): {row[4]}")
                        print(f"   滚动市销率(psTTM): {row[5]}")
                        print(f"   滚动市现率(pcfNcfTTM): {row[6]}")
                    else:
                        print(f"⚠️ 无数据返回")
                else:
                    print(f"❌ 查询失败: {rs.error_msg}")
                    
            except Exception as e:
                print(f"❌ 测试失败: {e}")
        
        # 登出
        bs.logout()
        print(f"\n✅ BaoStock直接API测试完成")
        
    except ImportError:
        print("❌ BaoStock未安装")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_baostock_provider_valuation():
    """测试BaoStock Provider的估值功能"""
    print("\n" + "=" * 60)
    print("🧪 测试BaoStock Provider估值功能")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.baostock_utils import get_baostock_provider
        
        provider = get_baostock_provider()
        
        # 测试股票代码
        test_symbols = ['600000', '000001', '600519']
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"📅 测试日期范围: {start_date} 到 {end_date}")
        
        for symbol in test_symbols:
            print(f"\n📊 测试股票: {symbol}")
            print("-" * 30)
            
            try:
                # 测试估值数据获取
                valuation_df = provider.get_valuation_data(symbol, start_date, end_date)
                
                if not valuation_df.empty:
                    print(f"✅ 估值数据获取成功: {len(valuation_df)}条记录")
                    print(f"   列名: {list(valuation_df.columns)}")
                    
                    # 显示最新数据
                    if len(valuation_df) > 0:
                        latest = valuation_df.iloc[-1]
                        print(f"   最新数据:")
                        print(f"     日期: {latest.get('date', 'N/A')}")
                        print(f"     收盘价: {latest.get('close', 'N/A')}")
                        print(f"     PE(TTM): {latest.get('peTTM', 'N/A')}")
                        print(f"     PB(MRQ): {latest.get('pbMRQ', 'N/A')}")
                        print(f"     PS(TTM): {latest.get('psTTM', 'N/A')}")
                        print(f"     PCF(TTM): {latest.get('pcfNcfTTM', 'N/A')}")
                else:
                    print(f"⚠️ 未获取到估值数据")
                    
            except Exception as e:
                print(f"❌ 测试失败: {e}")
        
        print(f"\n✅ BaoStock Provider估值测试完成")
        
    except Exception as e:
        print(f"❌ Provider测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_baostock_adapter_daily_basic():
    """测试BaoStock适配器的daily_basic功能"""
    print("\n" + "=" * 60)
    print("🧪 测试BaoStock适配器daily_basic功能")
    print("=" * 60)
    
    try:
        from app.services.data_source_adapters import BaoStockAdapter
        
        adapter = BaoStockAdapter()
        
        if not adapter.is_available():
            print("❌ BaoStock适配器不可用")
            return
        
        print("✅ BaoStock适配器可用")
        
        # 测试获取daily_basic数据
        trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print(f"📅 获取{trade_date}的daily_basic数据...")
        
        df = adapter.get_daily_basic(trade_date)
        
        if df is not None and not df.empty:
            print(f"✅ daily_basic数据获取成功: {len(df)}条记录")
            print(f"   列名: {list(df.columns)}")
            
            # 显示前几条记录
            print(f"\n📊 前5条记录:")
            for i, row in df.head().iterrows():
                print(f"   {i+1}. {row.get('ts_code', 'N/A')} - {row.get('name', 'N/A')}")
                print(f"      PE: {row.get('pe', 'N/A')}, PB: {row.get('pb', 'N/A')}")
                print(f"      收盘价: {row.get('close', 'N/A')}")
            
            # 统计有效数据
            pe_count = df['pe'].notna().sum() if 'pe' in df.columns else 0
            pb_count = df['pb'].notna().sum() if 'pb' in df.columns else 0
            
            print(f"\n📈 数据统计:")
            print(f"   有PE数据的股票: {pe_count}只")
            print(f"   有PB数据的股票: {pb_count}只")
            
        else:
            print(f"❌ 未获取到daily_basic数据")
        
        print(f"\n✅ BaoStock适配器测试完成")
        
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_data_source_manager_with_baostock():
    """测试数据源管理器中的BaoStock功能"""
    print("\n" + "=" * 60)
    print("🧪 测试数据源管理器中的BaoStock功能")
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
            
            # 测试fallback机制
            trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            print(f"📅 测试fallback机制获取{trade_date}数据...")
            
            df, source = manager.get_daily_basic_with_fallback(trade_date)
            
            if df is not None and not df.empty:
                print(f"✅ Fallback获取成功: {len(df)}条记录，来源: {source}")
                
                if source == 'baostock':
                    print(f"🎯 使用了BaoStock数据源!")
                    # 检查BaoStock特有的估值指标
                    if 'ps' in df.columns:
                        ps_count = df['ps'].notna().sum()
                        print(f"   市销率(PS)数据: {ps_count}只股票")
                    if 'pcf' in df.columns:
                        pcf_count = df['pcf'].notna().sum()
                        print(f"   市现率(PCF)数据: {pcf_count}只股票")
                else:
                    print(f"ℹ️ 使用了其他数据源: {source}")
            else:
                print(f"❌ Fallback获取失败")
        else:
            print(f"❌ 未找到BaoStock适配器")
        
        print(f"\n✅ 数据源管理器测试完成")
        
    except Exception as e:
        print(f"❌ 数据源管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_baostock_valuation_direct()
    test_baostock_provider_valuation()
    test_baostock_adapter_daily_basic()
    test_data_source_manager_with_baostock()
