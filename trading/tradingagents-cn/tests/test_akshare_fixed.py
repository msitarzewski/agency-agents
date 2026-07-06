#!/usr/bin/env python3
"""
测试修复后的AKShare功能
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

def test_akshare_adapter_fixed():
    """测试修复后的AKShare适配器"""
    print("=" * 60)
    print("🧪 测试修复后的AKShare适配器")
    print("=" * 60)
    
    try:
        from app.services.data_source_adapters import AKShareAdapter
        
        adapter = AKShareAdapter()
        
        if not adapter.is_available():
            print("❌ AKShare适配器不可用")
            return
        
        print("✅ AKShare适配器可用")
        
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
            print(f"   前10条记录:")
            for i, row in basic_df.head(10).iterrows():
                ts_code = row.get('ts_code', 'N/A')
                name = row.get('name', 'N/A')
                close = row.get('close', 'N/A')
                total_mv = row.get('total_mv', 'N/A')
                turnover_rate = row.get('turnover_rate', 'N/A')
                print(f"     {ts_code} - {name}")
                print(f"       收盘价: {close}, 总市值: {total_mv}, 换手率: {turnover_rate}")
            
            # 统计有效数据
            close_count = basic_df['close'].notna().sum() if 'close' in basic_df.columns else 0
            mv_count = basic_df['total_mv'].notna().sum() if 'total_mv' in basic_df.columns else 0
            turnover_count = basic_df['turnover_rate'].notna().sum() if 'turnover_rate' in basic_df.columns else 0
            
            # 统计非零数据
            close_nonzero = (basic_df['close'] > 0).sum() if 'close' in basic_df.columns else 0
            mv_nonzero = (basic_df['total_mv'] > 0).sum() if 'total_mv' in basic_df.columns else 0
            
            print(f"\n   📈 数据统计:")
            print(f"     有收盘价数据的股票: {close_count}只 (非零: {close_nonzero}只)")
            print(f"     有总市值数据的股票: {mv_count}只 (非零: {mv_nonzero}只)")
            print(f"     有换手率数据的股票: {turnover_count}只")
            
        else:
            print("❌ daily_basic数据获取失败")
        
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_data_source_manager_akshare():
    """测试数据源管理器中的AKShare"""
    print("\n" + "=" * 60)
    print("🧪 测试数据源管理器中的AKShare")
    print("=" * 60)
    
    try:
        from app.services.data_source_adapters import DataSourceManager
        
        manager = DataSourceManager()
        available_adapters = manager.get_available_adapters()
        
        print(f"✅ 可用数据源: {[adapter.name for adapter in available_adapters]}")
        
        # 查找AKShare适配器
        akshare_adapter = None
        for adapter in available_adapters:
            if adapter.name == 'akshare':
                akshare_adapter = adapter
                break
        
        if akshare_adapter:
            print(f"✅ 找到AKShare适配器，优先级: {akshare_adapter.priority}")
            
            # 测试fallback机制
            trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            print(f"📅 测试fallback机制获取{trade_date}数据...")
            
            df, source = manager.get_daily_basic_with_fallback(trade_date)
            
            if df is not None and not df.empty:
                print(f"✅ Fallback获取成功: {len(df)}条记录，来源: {source}")
                
                if source == 'akshare':
                    print(f"🎯 使用了AKShare数据源!")
                    # 检查AKShare特有的数据
                    if 'total_mv' in df.columns:
                        mv_count = df['total_mv'].notna().sum()
                        print(f"   总市值数据: {mv_count}只股票")
                    if 'turnover_rate' in df.columns:
                        turnover_count = df['turnover_rate'].notna().sum()
                        print(f"   换手率数据: {turnover_count}只股票")
                else:
                    print(f"ℹ️ 使用了其他数据源: {source}")
            else:
                print(f"❌ Fallback获取失败")
        else:
            print(f"❌ 未找到AKShare适配器")
        
    except Exception as e:
        print(f"❌ 数据源管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_akshare_adapter_fixed()
    test_data_source_manager_akshare()
