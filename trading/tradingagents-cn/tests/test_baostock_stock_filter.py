#!/usr/bin/env python3
"""
测试BaoStock股票过滤功能
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

def test_baostock_stock_types():
    """测试BaoStock返回的不同类型数据"""
    print("=" * 60)
    print("🔍 测试BaoStock返回的不同类型数据")
    print("=" * 60)
    
    try:
        import baostock as bs
        
        # 登录BaoStock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ BaoStock登录失败: {lg.error_msg}")
            return
        
        print("✅ BaoStock登录成功")
        
        # 获取股票列表
        trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 查询日期: {trade_date}")
        
        rs = bs.query_all_stock(day=trade_date)
        print(f"返回码: {rs.error_code}")
        print(f"返回消息: {rs.error_msg}")
        print(f"字段列表: {rs.fields}")
        
        if rs.error_code == '0':
            # 解析数据并按类型分类
            type_counts = {}
            stock_samples = {}
            count = 0
            
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                count += 1
                
                if len(row) >= 5:
                    code = row[0]
                    name = row[1]
                    stock_type = row[4]
                    
                    # 统计各类型数量
                    if stock_type not in type_counts:
                        type_counts[stock_type] = 0
                        stock_samples[stock_type] = []
                    
                    type_counts[stock_type] += 1
                    
                    # 保存前3个样本
                    if len(stock_samples[stock_type]) < 3:
                        stock_samples[stock_type].append((code, name))
                
                if count >= 1000:  # 限制处理数量
                    break
            
            print(f"\n📊 数据类型统计 (前{count}条记录):")
            type_names = {
                '1': '股票',
                '2': '指数', 
                '3': '其它',
                '4': '可转债',
                '5': 'ETF'
            }
            
            for stock_type, count in type_counts.items():
                type_name = type_names.get(stock_type, f'未知类型({stock_type})')
                print(f"   类型{stock_type} ({type_name}): {count}条")
                
                # 显示样本
                if stock_type in stock_samples:
                    print(f"     样本:")
                    for code, name in stock_samples[stock_type]:
                        print(f"       {code} - {name}")
                print()
        
        bs.logout()
        print("✅ BaoStock登出成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_baostock_adapter_stock_filter():
    """测试修复后的BaoStock适配器股票过滤"""
    print("\n" + "=" * 60)
    print("🧪 测试修复后的BaoStock适配器股票过滤")
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
            
            # 检查是否都是股票
            print(f"\n   前10条记录:")
            for i, row in df.head(10).iterrows():
                symbol = row.get('symbol', 'N/A')
                name = row.get('name', 'N/A')
                ts_code = row.get('ts_code', 'N/A')
                print(f"     {symbol} - {name} - {ts_code}")
            
            # 检查股票代码格式
            print(f"\n   📊 股票代码分析:")
            if 'symbol' in df.columns:
                # 分析股票代码前缀
                prefixes = df['symbol'].str[:3].value_counts()
                print(f"     股票代码前缀分布:")
                for prefix, count in prefixes.head(10).items():
                    print(f"       {prefix}xxx: {count}只")
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
                pe = row.get('pe', 'N/A')
                pb = row.get('pb', 'N/A')
                close = row.get('close', 'N/A')
                print(f"     {ts_code} - {name}")
                print(f"       PE: {pe}, PB: {pb}, 收盘价: {close}")
            
            # 统计有效数据
            pe_count = basic_df['pe'].notna().sum() if 'pe' in basic_df.columns else 0
            pb_count = basic_df['pb'].notna().sum() if 'pb' in basic_df.columns else 0
            close_count = basic_df['close'].notna().sum() if 'close' in basic_df.columns else 0
            
            # 统计非零数据
            pe_nonzero = (basic_df['pe'] > 0).sum() if 'pe' in basic_df.columns else 0
            pb_nonzero = (basic_df['pb'] > 0).sum() if 'pb' in basic_df.columns else 0
            
            print(f"\n   📈 数据统计:")
            print(f"     有PE数据的股票: {pe_count}只 (非零: {pe_nonzero}只)")
            print(f"     有PB数据的股票: {pb_count}只 (非零: {pb_nonzero}只)")
            print(f"     有收盘价数据的股票: {close_count}只")
            
        else:
            print("❌ daily_basic数据获取失败")
        
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_baostock_stock_types()
    test_baostock_adapter_stock_filter()
