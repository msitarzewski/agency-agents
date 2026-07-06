#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试从通达信获取股票代码和名称
"""

import pytest
pytest.importorskip("enhanced_stock_list_fetcher")
pytestmark = pytest.mark.integration

from enhanced_stock_list_fetcher import enhanced_fetch_stock_list

def test_get_stock_codes():
    """
    测试获取股票代码和名称
    """
    print("=" * 60)
    print("📊 测试从通达信获取股票代码和名称")
    print("=" * 60)

    try:
        # 获取股票数据
        print("\n🔄 正在获取股票数据...")
        stock_data = enhanced_fetch_stock_list(
            type_='stock',  # 只获取股票
            enable_server_failover=True,  # 启用故障转移
            max_retries=3
        )

        if stock_data is not None and not stock_data.empty:
            print(f"\n✅ 成功获取到 {len(stock_data)} 只股票")

            # 显示前20只股票的代码和名称
            print("\n📋 前20只股票代码和名称:")
            print("-" * 40)
            print(f"{'股票代码':<10} {'股票名称':<15} {'市场'}")
            print("-" * 40)

            for i, (idx, row) in enumerate(stock_data.head(20).iterrows()):
                market = "深圳" if row['sse'] == 'sz' else "上海"
                print(f"{row['code']:<10} {row['name']:<15} {market}")

            # 统计信息
            print("\n📊 统计信息:")
            print("-" * 30)
            sz_count = len(stock_data[stock_data['sse'] == 'sz'])
            sh_count = len(stock_data[stock_data['sse'] == 'sh'])
            print(f"深圳市场股票: {sz_count} 只")
            print(f"上海市场股票: {sh_count} 只")
            print(f"总计股票数量: {len(stock_data)} 只")

            # 保存到文件
            output_file = "stock_codes_list.csv"
            stock_codes_df = stock_data[['code', 'name', 'sse']].copy()
            stock_codes_df['market'] = stock_codes_df['sse'].apply(lambda x: '深圳' if x == 'sz' else '上海')
            stock_codes_df = stock_codes_df[['code', 'name', 'market']]
            stock_codes_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n💾 股票代码列表已保存到: {output_file}")

        else:
            print("❌ 未能获取到股票数据")

    except Exception as e:
        print(f"❌ 获取股票数据时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_stock_codes()